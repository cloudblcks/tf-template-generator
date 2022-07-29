FROM public.ecr.aws/lambda/python:3.10.4

# Copy function code
COPY . ${LAMBDA_TASK_ROOT}
# COPY templates_map.json ${LAMBDA_TASK_ROOT}

# Install the function's dependencies using file requirements.txt
# from your project folder.

COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "aws_lambda.lambda_handler_new" ]