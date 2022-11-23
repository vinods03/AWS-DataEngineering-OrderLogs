import sys, boto3, json
from pg import DB
s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')
secretsmanager = boto3.client(service_name = 'secretsmanager', region_name = 'us-east-1')

secret_holder_name = 'my-order-logs-cluster-details'
get_secret_response = secretsmanager.get_secret_value(SecretId = secret_holder_name)
credentials = json.loads(get_secret_response['SecretString'])
username = credentials['username']
password = credentials['password']
host = credentials['host']

db = DB(dbname = 'dev', host = host, port = 5439, user = username, passwd = password)

load_query = """
            begin;
            
            copy main_data.my_order_logs from 's3://my-order-logs-bucket-staging/'
            iam_role 'arn:aws:iam::100163808729:role/MyRedshiftRoleWithAdminAccess'
            CSV QUOTE '\"' DELIMITER ','
			acceptinvchars;
			
			end;
		"""

print('The load query is ', load_query)

BUCKET = 'my-order-logs-bucket-staging'
response = s3.list_objects_v2(Bucket = BUCKET)
print(response)

try:
    db.query(load_query)
    for object in response['Contents']:
        bucket_name = 'my-order-logs-bucket-staging'
        file_name = object['Key']
        file_size = str(object['Size']/1000)
        file_etag = object['ETag']
       
        try: 
            dynamodb.put_item(
                         TableName = 'my-order-logs-files-processed', 
                         Item = {'file_name': {'S': file_name}, 'bucket_name': {'S': bucket_name}, 'file_size': {'S': file_size}, 'file_etag': {'S': file_etag}}
                         )
            print('DynamoDB audit entry for ', file_name, ' completed' )
        
            try:       
                s3.delete_object(Bucket = BUCKET, Key = file_name)
            except Exception as e:
                print('S3 delete failed with exception: ', e)
     
        except Exception as f:
                print('Dynamo DB audit entry for ', file_name, ' failed !!', ' The exception is ', f)
                
except Exception as g:
    print('Redshift load failed with exception ', g)
     
          