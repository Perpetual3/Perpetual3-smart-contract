# Perpetual3 Smart Contract

Full high level documentations: https://perpetualweb3.gitbook.io

# def claimPerpetual():
- Allows the owner of a Perpetual ID to transfer the related NFT from the contract to their own wallet
```
def claimPerpetual():

    perpetualID = Txn.assets[0]

    ownershipCheck = AssetParam.reserve(perpetualID)

    return Seq(

        ownershipCheck,

        Assert(ownershipCheck.hasValue()),
        Assert(ownershipCheck.value() == Txn.sender()),
        ...
```

# def perpetualGenesis():
- Allows the creation of a Perpetual ID that will contain metadata needed to download the Perpetual File from the blockchain

```
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
        ...
```

# def safeWithdraw():
- Allows the creator address to safely withdraw funds from the contract without creating denial of service
```
...
    amount = Btoi(Txn.application_args[1])
    appBalance = Balance(Global.current_application_address())
    safeminappBalance = MinBalance(
        Global.current_application_address())+Int(1000000)

    return Seq(

        Assert((appBalance-amount) >= safeminappBalance),
        Assert(Txn.sender() == Global.creator_address()),
...
```

# def changeFee():
- Allows the creator address to safely change platform fees without creating denial of service
```
...
     newFee = Btoi(Txn.application_args[1])

    return Seq(
        Assert(newFee <= Int(5000000)),
        Assert(Txn.sender() == Global.creator_address()),
        App.globalPut(Bytes("Perpetual Fee"), newFee)
    )
...
```

# OnComplete.UpdateApplication
To ensure the best immutability and security to the platform the application cannot be updated

# OnComplete.DeleteApplication
To ensure the best immutability and security to the platform the application cannot be deleted
       
