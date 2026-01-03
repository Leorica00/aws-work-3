import boto3
from botocore.exceptions import ClientError
from os import getenv
import json

sqs_client = boto3.client(
  "sqs",
  aws_access_key_id=getenv("aws_access_key_id"),
  aws_secret_access_key=getenv("aws_secret_access_key"),
  aws_session_token=getenv("aws_session_token"),
  region_name=getenv("aws_region_name")
)


def create_queue(name):
  # Check if the queue already exists
  response = sqs_client.list_queues(QueueNamePrefix=name)
  if 'QueueUrls' in response:
    print("Queue already exists:", response['QueueUrls'][0])
    return

  # Create the queue if it doesn't exist
  response = sqs_client.create_queue(QueueName=name,
                                     Attributes={
                                       "DelaySeconds":
                                       str(5),
                                       "MessageRetentionPeriod":
                                       str(60 * 60 * 24),
                                       "VisibilityTimeout":
                                       str(60),
                                       "FifoQueue":
                                       "true",
                                     })
  print(response)


def list_queues():
  response = sqs_client.list_queues()
  for queue in response.get("QueueUrls"):
    print(queue)


def display_queue_configuration(url):
  response = sqs_client.get_queue_attributes(QueueUrl=url,
                                             AttributeNames=["All"])
  attributes = response.get("Attributes")
  print(attributes)


def update_queue_configuration(url):
  sqs_client.set_queue_attributes(QueueUrl=url,
                                  Attributes={"DelaySeconds": "3"})
  print("Queue Updated")


def send_message(url, data):
  body = json.dumps(data)
  response = sqs_client.send_message(QueueUrl=url,
                                     MessageBody=body,
                                     MessageGroupId="default",
                                     MessageDeduplicationId="1234")
  print(response)


def receive_queue_message(queue_url):
  """
   Retrieves one or more messages (up to 10), from the specified queue.
   """
  try:
    response = sqs_client.receive_message(QueueUrl=queue_url)
    return response
  except ClientError:
    print("ERROR", f"Could not receive the message from the - {queue_url}.")
    return None


def delete_queue_message(queue_url, receipt_handle):
  """
   Deletes the specified message from the specified queue.
   """
  try:
    response = sqs_client.delete_message(QueueUrl=queue_url,
                                         ReceiptHandle=receipt_handle)
  except ClientError:
    print("ERROR", f"Could not delete the meessage from the - {queue_url}.")

  else:
    return response


def to_queue_url(name):
  response = sqs_client.get_queue_url(QueueName=name)
  return response.get("QueueUrl")


def receive_and_delete_message(queue_url):

  try:
    # Receive one message from the queue
    response = sqs_client.receive_message(QueueUrl=queue_url)

    if 'Messages' in response:
      message = response['Messages'][0]
      receipt_handle = message['ReceiptHandle']

      # Delete the received message from the queue
      sqs_client.delete_message(QueueUrl=queue_url,
                                ReceiptHandle=receipt_handle)
      print("deleted")
      print(response)
      return message
    else:
      return None

  except ClientError as e:
    print(
      "ERROR:",
      f"Could not receive or delete the message from the queue - {queue_url}.")
    print("Error message:", e)
    return None


def purge_queue(url):
  response = sqs_client.purge_queue(QueueUrl=url)
  print("purged", response)


def delete_queue(url):
  response = sqs_client.delete_queue(QueueUrl=url)
  print("deleted", response)


def main():
#   QUEUE_NAME = "firstQueueTest.fifo"
#   create_queue(QUEUE_NAME)
  QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/598373074862/firstQueueTest.fifo"
  # print(f"generated: {QUEUE_URL}")

#   list_queues()

#   display_queue_configuration(QUEUE_URL)

#   update_queue_configuration(QUEUE_URL)

#   display_queue_configuration(QUEUE_URL)

#   send_message(QUEUE_URL, {"test": "data"})
  send_message(QUEUE_URL, {"image": "https://static.my.ge/myauto/photos/7/7/2/8/9/large/92982778_1.jpg?v=1"})

  receive_and_delete_message(QUEUE_URL)

  # purge_queue(QUEUE_URL)

  # delete_queue(QUEUE_URL)


if __name__ == "__main__":
  main()
