import time
from os import getenv
from dotenv import load_dotenv
import argparse
from auth import aws_client
from vpc import create_vpc, add_name_tag, get_or_set_igw, create_route_table_without_route, create_subnet, associate_route_table_to_subnet, create_route_table_with_route, enable_auto_public_ips
from ec2 import create_key_pair, create_security_group, add_ssh_access_sg, run_ec2
from rds import create_db_subnet_group, create_rds_security_group, create_db_instance

load_dotenv()

def main():
    # Names configuration
    vpc_name = "vpc_name"
    private_subnet_name_1 = "private_subnet_name_1"
    private_subnet_name_2 = "private_subnet_name_2"
    public_subnet_name_1 = "public_subnet_name_1"
    route_table_name = "my_route_name"
    key_name = "key_name"
    ec2_sg_name = "ec2_name-sg"
    ec2_sg_description = "Security group to enable access on ec2"
    ec2_name = "ec2_name"
    rds_sg_name = "ec2_name_automated-sg-rds"

    ec2_client = aws_client('ec2')
    vpc_id = create_vpc(ec2_client, '10.0.0.0/16')
    add_name_tag(ec2_client, vpc_id, vpc_name)
    get_or_set_igw(ec2_client, vpc_id)

    private_subnets = []
    # create private subnet
    subnet_id = create_subnet(ec2_client, vpc_id, '10.0.0.0/24', private_subnet_name_1, 'us-east-1a')
    rtb_id = create_route_table_without_route(ec2_client, vpc_id)
    associate_route_table_to_subnet(ec2_client, rtb_id, subnet_id)
    private_subnets.append(subnet_id)

    subnet_id = create_subnet(ec2_client, vpc_id, '10.0.1.0/24', private_subnet_name_2, 'us-east-1b')
    rtb_id = create_route_table_without_route(ec2_client, vpc_id)
    time.sleep(5)
    associate_route_table_to_subnet(ec2_client, rtb_id, subnet_id)
    private_subnets.append(subnet_id)
    print(f'private subnets : {private_subnets}')

    # public subnet
    subnet_id = create_subnet(ec2_client, vpc_id, '10.0.2.0/24', public_subnet_name_1, 'us-east-1a')
    rtb_id = create_route_table_with_route(ec2_client, vpc_id, route_table_name, get_or_set_igw(ec2_client, vpc_id))
    time.sleep(5)
    associate_route_table_to_subnet(ec2_client, rtb_id, subnet_id)
    enable_auto_public_ips(ec2_client, subnet_id, 'enable')

    # create key pair
    create_key_pair(ec2_client, key_name)

    # create ec2 sg
    ec2_security_group_id = create_security_group(ec2_client, ec2_sg_name, ec2_sg_description, vpc_id)

    # only concrete ip rule
    add_ssh_access_sg(ec2_client, ec2_security_group_id)

    # EC2
    run_ec2(ec2_client, ec2_security_group_id, subnet_id, ec2_name)

    # RDS - Postgres
    rds_client = aws_client('rds')

    # SG for RDS
    rds_subnet_group = create_db_subnet_group(rds_client, rds_sg_name, vpc_id, private_subnets)
    print("switched to ec2")
    rds_sg_id = create_rds_security_group(ec2_client, rds_sg_name, vpc_id, ec2_security_group_id)

    create_db_instance(rds_client, rds_sg_id, rds_subnet_group)

if __name__ == "__main__":
    main()