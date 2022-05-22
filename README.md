# tf-template-generator

## How to prepare Docker image for the lambda function

Run the following in the `tf_generator/` directory: 
```
docker build -t tf-generator .
```

## How to test locally the lambda Docker image

When the image is build, it is possible to test it locally. 

1. First, run the image using the following command (from inside the `tf_generator/` directory):

```
docker run -p 9000:8080 tf-generator 
```

2. Test your application locally using the runtime interface emulator. From a new terminal window, post an event to the following endpoint using a curl command:

```
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'
```

This command invokes the function running in the container image and returns a response.

## How to deploy on AWS

1. (Optional) Login to Terraform Cloud by running 

```
terraform login
```

And following the instructions. 

2. Plan the deployment by running 

```
terraform plan
```

in the root folder of the project. 

3. If the plan looks appropriate, run

```
terraform apply
```

to deploy the code. 