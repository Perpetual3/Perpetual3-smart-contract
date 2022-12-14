from pyteal import *

#defined constants for app call 
class Constants:
    genesisA = Bytes("ptr")
    claimA = Bytes("perpetualClaim")
    changeFeeA = Bytes("changefee")
    safewithdraA = Bytes("safewithdraw")

#safely withdraw funds from contract to creator address without creating denial of service
@ Subroutine(TealType.none)
def safeWithdraw():
    #get amount requested in app args
    amount = Btoi(Txn.application_args[1])
    #get app balance
    appBalance = Balance(Global.current_application_address())
    #get min balance + add 1 algo for more security
    safeminappBalance = MinBalance(
        Global.current_application_address())+Int(1000000)

    return Seq(
        #Check appBalance-amount is more or equal to min balance + 1 algo
        Assert((appBalance-amount) >= safeminappBalance),
        Assert(Txn.sender() == Global.creator_address()),
        #Transfer requested amount from app to creator
        InnerTxnBuilder.Begin(),

        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.Payment,
            TxnField.sender: Global.current_application_address(),
            TxnField.receiver: Global.creator_address(),
            TxnField.amount: amount
        }),
        InnerTxnBuilder.Submit(),
    )


@ Subroutine(TealType.none)
def changeFee():
    #Get requested new fee from creator
    newFee = Btoi(Txn.application_args[1])

    return Seq(
        #Check that the fee doesn't exceed 5 algos
        Assert(newFee <= Int(5000000)),
        #Check the sender is the creator
        Assert(Txn.sender() == Global.creator_address()),
        App.globalPut(Bytes("Perpetual Fee"), newFee)
    )


@ Subroutine(TealType.none)
def claimPerpetual():
    #get asset id from foreign assets
    perpetualID = Txn.assets[0]
    #get the reserve account which is set at the creation of PerpetualID as the PerpetualID owner
    ownershipCheck = AssetParam.reserve(perpetualID)

    return Seq(

        ownershipCheck,

        Assert(ownershipCheck.hasValue()),
        Assert(ownershipCheck.value() == Txn.sender()),

        InnerTxnBuilder.Begin(),

        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.AssetTransfer,
            TxnField.xfer_asset: perpetualID,
            TxnField.asset_amount: Int(1),
            TxnField.asset_sender: Global.current_application_address(),
            TxnField.asset_receiver: Txn.sender(),
        }),
        InnerTxnBuilder.Submit(),

    )


@ Subroutine(TealType.none)
def perpetualGenesis():
    
    #get current active platform fee
    perpetualFee = App.globalGetEx(
        App.id(), Bytes("Perpetual Fee"))
    
    #get perpetual File metadata
    fullname = Txn.application_args[1]
    #learn more on unitname on documentations
    unitname = Txn.application_args[2]
    #get sha256 hash of file
    integrity = Txn.application_args[3]

    return Seq(
        perpetualFee,
        Assert(Gtxn[1].receiver() == Global.current_application_address()),
        Assert(perpetualFee.hasValue()),
        Assert(Gtxn[1].amount() == perpetualFee.value()),

        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.AssetConfig,
            TxnField.config_asset_default_frozen: Int(0),
            TxnField.config_asset_decimals: Int(0),
            TxnField.config_asset_unit_name: unitname,
            TxnField.config_asset_name: fullname,
            TxnField.config_asset_reserve: Txn.sender(),
            TxnField.config_asset_clawback: Global.current_application_address(),
            TxnField.config_asset_total: Int(1),
            TxnField.config_asset_decimals: Int(0),
            TxnField.config_asset_url: Bytes(""),
            TxnField.config_asset_metadata_hash: integrity
        }),
        InnerTxnBuilder.Submit(),
    )


def approval_program():

    initialize = Seq([
        # On init you may create the ASA
        Assert(Txn.type_enum() == TxnType.ApplicationCall),
        # Check arg len 1
        Assert(Txn.application_args.length() == Int(0)),
        Approve()
    ])

    genesis = Seq(
        Assert(Txn.close_remainder_to() == Global.zero_address()),
        Assert(Txn.rekey_to() == Global.zero_address()),
        perpetualGenesis(),
        Approve()
    )

    claim = Seq(
        Assert(Txn.close_remainder_to() == Global.zero_address()),
        Assert(Txn.rekey_to() == Global.zero_address()),
        claimPerpetual(),
        Approve()
    )

    changefee = Seq(
        changeFee(),
        Approve()
    )

    safewithdraw = Seq(
        safeWithdraw(),
        Approve()
    )

    # onCall Sequence
    # Checks that the first transaction is an Application call, and that there is at least 1 argument.
    # Then it checks the first argument of the call. The first argument must be a valid value between
    # "setupSale", "buy", "executeTransfer", "refund" and "claimFees"
    onCall = If(Txn.application_args[0] == Constants.genesisA).Then(genesis)  \
        .ElseIf(Txn.application_args[0] == Constants.claimA).Then(claim)  \
        .ElseIf(Txn.application_args[0] == Constants.changeFeeA).Then(changefee)  \
        .ElseIf(Txn.application_args[0] == Constants.safewithdraA).Then(safewithdraw)  \
        .Else(Approve())

    # Check the transaction type and execute the corresponding code
    #   1. If application_id() is 0 then the program has just been created, so we initialize it
    #   2. If on_completion() is 0 we execute the onCall code
    return If(Txn.application_id() == Int(0)).Then(initialize)                  \
        .ElseIf(Txn.on_completion() == OnComplete.CloseOut).Then(Reject()) \
        .ElseIf(Txn.on_completion() == OnComplete.UpdateApplication).Then(Reject()) \
        .ElseIf(Txn.on_completion() == OnComplete.DeleteApplication).Then(Reject()) \
        .ElseIf(Txn.on_completion() == OnComplete.ClearState).Then(Reject()) \
        .ElseIf(Txn.on_completion() == OnComplete.OptIn).Then(Approve())    \
        .ElseIf(Txn.on_completion() == Int(0)).Then(onCall)                 \
        .Else(Reject())


def clear_program():
    return Approve()


if __name__ == "__main__":
    # Compiles the approval program
    with open("approval.teal", "w+") as f:
        compiled = compileTeal(
            approval_program(), mode=Mode.Application, version=6)
        f.write(compiled)

    # Compiles the clear program
    with open("clear.teal", "w+") as f:
        compiled = compileTeal(
            clear_program(), mode=Mode.Application, version=6)
        f.write(compiled)
