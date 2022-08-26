from pyteal import *


class Constants:
    genesisA = Bytes("ptr")
    claimA = Bytes("perpetualClaim")
    changeFeeA = Bytes("changefee")
    safewithdraA = Bytes("safewithdraw")


@ Subroutine(TealType.none)
def safeWithdraw():

    amount = Btoi(Txn.application_args[1])
    appBalance = Balance(Global.current_application_address())
    safeminappBalance = MinBalance(
        Global.current_application_address())+Int(1000000)

    return Seq(

        Assert((appBalance-amount) >= safeminappBalance),
        Assert(Txn.sender() == Global.creator_address()),

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
    newFee = Btoi(Txn.application_args[1])

    return Seq(
        Assert(newFee <= Int(5000000)),
        Assert(Txn.sender() == Global.creator_address()),
        App.globalPut(Bytes("Perpetual Fee"), newFee)
    )


@ Subroutine(TealType.none)
def claimPerpetual():

    perpetualID = Txn.assets[0]

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

    perpetualFee = App.globalGetEx(
        App.id(), Bytes("Perpetual Fee"))

    fullname = Txn.application_args[1]
    unitname = Txn.application_args[2]
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
