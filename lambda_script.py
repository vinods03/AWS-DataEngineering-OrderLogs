import boto3, json, time

def lambda_handler(event, context):
    
    print(event)
    
    s3 = boto3.resource('s3')
    glue = boto3.client('glue')
    target_bucket_name = 'my-order-logs-bucket-staging'
    crawler_name = 'my-order-logs-crawler'
    
    for i in event['Records']:
        
        source_bucket_name = i['s3']['bucket']['name']
        source_file_path = i['s3']['object']['key']
        source_file_name = source_file_path.split('/')[-1]
        source_file_size = str(i['s3']['object']['size']/1000)
        source_file_etag = i['s3']['object']['eTag']
        target_file_s3_url = 's3://' + target_bucket_name + '/' + source_file_name
        
        print('Name of the source bucket is: ', source_bucket_name)
        print('Name of the target bucket is: ', target_bucket_name)
        print('Source file path is: ', source_file_path)
        print('Name of the file uploaded is: ', source_file_name)
        print('Size of the file uploaded in KB is: ', source_file_size)
        print('ETag of the file uploaded is: ', source_file_etag)
        print('S3 Uri for the staging file is: ', target_file_s3_url)
   
        # move the file to a staging area with a static path to make the redshift copy command easier
       
        try:
            s3.Object(target_bucket_name, source_file_name).copy_from(CopySource = source_bucket_name + '/' + source_file_path)
            # s3.Object(source_bucket_name, source_file_path).delete()
            # We want to retain the files in landing area for a week, to enable users to query incoming order logs in near real time
            print('Successfully moved ', source_bucket_name, '/', source_file_path, ' to ', target_bucket_name)
        except Exception as e:
            print('Unable to move the file ', source_file_name, ' from landing area to staging area')
    
    try:        
        glue.start_crawler(Name = crawler_name)
    except Exception as f:
        print('Unable to start the glue crawler ', crawler_name, '. The exception is ', f)
    
   