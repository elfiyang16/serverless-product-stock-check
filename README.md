# Serverless Product Stock Check

This is a script snippet that will

- download the file from google sheet using _GoogleSheetAPI_
<img src="https://user-images.githubusercontent.com/29664811/108118059-b4c24280-7095-11eb-9ac2-ea640b0a8ab5.png" width="600">

- upload to s3 bucket
<img src="https://user-images.githubusercontent.com/29664811/108119220-61e98a80-7097-11eb-8986-1d2c236aac99.png" width="600">

- or,save as json file with datetime tag to local folder `downloaded` for future analysis (why json? maybe it will be used by JavaScript haha)
```json
{"Name":{"0":"screen","1":"keyboard","2":"mouse"},"Quantity ":{"0":3,"1":5,"2":10},"Vendor":{"0":"Elfi","1":"Julia","2":"Jone"},"Vendor_Email":{"0":"elfi@test.io","1":"julia@test.io","2":"jone@test.io"},"Attributes":{"0":"red","1":"blue","2":"yellow"}}
```
You can invoke the above part using the `./runPython.sh`, this will run the script as docker container. For the first time remember to build the image first.

The rest part is a python lambda function to:

- download the file from s3 bucket 

- run some check, aka. whethe any product stock level has fail to 0, and create a json file from that

- upload to s3 bucket 
<img src="https://user-images.githubusercontent.com/29664811/108118477-4df15900-7096-11eb-9176-45ff00047cdc.png" width="600">

This part is built and deployed using `serverless` framework.
<img src="https://user-images.githubusercontent.com/29664811/108119530-db817880-7097-11eb-8704-06c578bbf29c.png" width="600">

Install `serverless` npm package globally and `sls deploy` to deploy, `sls invoke --function stock-check` to invoke, and `sls remove` to delete the stack. 

Currently a lot more refactoring to be done. Ideally I would like to create a Producer-Consumer workflow to allow _Stock-Check` worker to send messages to SQS queue,
and then MyConsumerFunction receives and processes messages from queue and maybe push notification through some Twilio API:
`lambda(MyJobFunction) -> sqs(my-queue) -> lambda(MyConsumerFunction)`

