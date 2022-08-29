# Perpetual3 Smart Contract

Full high level documentations: https://perpetualweb3.gitbook.io

# def changeFee():

# def claimPerpetual():

# def perpetualGenesis():

# def safeWithdraw():
- Allows the creator address to safely withdraw funds from the contract without creating denial of service
- Ensures that Amount requested
- 
```
    amount = Btoi(Txn.application_args[1])
    appBalance = Balance(Global.current_application_address())
    safeminappBalance = MinBalance(
        Global.current_application_address())+Int(1000000)

    return Seq(

        Assert((appBalance-amount) >= safeminappBalance),
        Assert(Txn.sender() == Global.creator_address()),
```

# OnComplete.UpdateApplication

# OnComplete.DeleteApplication

# OnComplete.ClearState

# OnComplete.CloseOut
       
