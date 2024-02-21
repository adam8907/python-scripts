# Import HAR and frontend site functionality 
# Author: Adamski Molina
# mail: adams8907@gmail.com
# Version: 1.0

import paramiko
import sys
import argparse
import json 
from urllib.parse import urlparse
import os
from scp import SCPClient
import base64

args = ""

def usage():
    parser = argparse.ArgumentParser(description = 'Script to create a site using a HAR file')

    parser.add_argument('--har', '-H', type=str, required=True)
    parser.add_argument('--username', '-u', type=str, required=True)
    parser.add_argument('--password', '-p', type=str, required=True)
    parser.add_argument('--server', '-s', type=str, required=True)
    parser.add_argument('--protocol', '-P', type=str, required=False, default="http", choices=['http','https'])

    return parser.parse_args()


def connect_to_server(hostname,username,password,port=22):
    # Create an SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
    # Connect to the server
        ssh.connect(hostname, port, username, password)
    except:
        print("Error, not able to connect to server")
    return ssh 

def parse_HAR(har_file):

    with open(har_file, 'r') as file_content:
        har_json = file_content.read()
    har_json = json.loads(har_json)
    list_hostnames = []
    for request in har_json['log']['entries']:
        print(f"Processing URL {request['request']['url']}")
        hostname = urlparse(request['request']['url']).netloc
        if hostname not in list_hostnames:
            list_hostnames.append(hostname)
        if request['response']['status'] == 200 and "googleapi" not in hostname and "TSbd" not in request['request']['url']:            
            path = os.path.dirname(urlparse(request['request']['url']).path)
            file_name = os.path.basename(urlparse(request['request']['url']).path)
            if 'text' in request['response']['content'] and  request['response']['content']['text'] != "" :
                content = request['response']['content']['text']
                b64_enc = 0
                if 'encoding' in request['response']['content']:
                    content = base64.b64decode(content)
                    b64_enc = 1
                if file_name == "":
                    file_name = "index.html"
                create_dir_structure(hostname, path, file_name, content, b64_enc)
            else:
                print(f"{request['request']['url']} is cached and does not have content data, skipping creation")
    for hostname in list_hostnames:
        create_site_apache(hostname)
    print("If you wanna try the site is working please add the following to your hosts files")
    print(f"{args.server}   {list_hostnames}")


def create_dir_structure(hostname, path, file_name, content, b64_enc):
    global args
    ssh = connect_to_server(args.server,args.username,args.password)
    
    if not (os.path.exists(path) and os.path.isdir(path)) or path == "/":
        print(f"Creating directory {path}")
        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p /var/www/html/{hostname.replace('.','_')}{path}")
    print(f"Creating file {file_name}")
    if b64_enc == 1:
         with open(file_name,'wb') as int_file:
            int_file.write(content)
    else:
        with open(file_name,'w') as int_file:
            int_file.write(content)
    with SCPClient(ssh.get_transport()) as scp_client:
        scp_client.put(f"./{file_name}", f"/var/www/html/{hostname.replace('.','_')}{path}/{file_name}")
    #stdin, stdout, stderr = ssh.exec_command(f"echo -e '{content}' > /var/www/html/{hostname.replace('.','_')}{path}/{file_name}")
    #print(stderr.read().decode('utf-8'))
    ssh.close()


def create_site_apache(hostname):
    global args
    
    APACHE_LOG_DIR = "{APACHE_LOG_DIR}"
    https_template = f"""<IfModule mod_ssl.c>
        <VirtualHost *:443>
                ServerAdmin webmaster@localhost
                ServerName {hostname}
                DocumentRoot /var/www/html/{hostname.replace('.','_')}
                ErrorLog ${APACHE_LOG_DIR}/error.log
                CustomLog ${APACHE_LOG_DIR}/access.log combined
                SSLEngine on
                SSLCertificateFile      /etc/ssl/certs/{hostname}.crt
                SSLCertificateKeyFile /etc/ssl/private/{hostname}.key
                <FilesMatch "\.(cgi|shtml|phtml|php)$">
                                SSLOptions +StdEnvVars
                </FilesMatch>
                <Directory /usr/lib/cgi-bin>
                                SSLOptions +StdEnvVars
                </Directory>
        </VirtualHost>
</IfModule>"""
    http_template = f"""
        <VirtualHost *:80>
                ServerAdmin webmaster@localhost
                ServerName {hostname}
                DocumentRoot /var/www/html/{hostname.replace('.','_')}
                ErrorLog ${APACHE_LOG_DIR}/error.log
                CustomLog ${APACHE_LOG_DIR}/access.log combined
                <FilesMatch "\.(cgi|shtml|phtml|php)$">
                                SSLOptions +StdEnvVars
                </FilesMatch>                
        </VirtualHost>
        """
    ssh = connect_to_server(args.server,args.username,args.password)
    if args.protocol == 'https':
        create_certs(hostname)
        print(f"Creating apache site conf for {hostname}")
        stdin, stdout, stderr = ssh.exec_command(f"echo -e '{https_template}' > /etc/apache2/sites-available/{hostname.replace('.','_')}.conf")
        print(stderr.read().decode('utf-8'))
    else:
        print(f"Creating apache site conf for {hostname}")
        stdin, stdout, stderr = ssh.exec_command(f"echo -e '{http_template}' > /etc/apache2/sites-available/{hostname.replace('.','_')}.conf")
        print(stderr.read().decode('utf-8'))
    print(f"Enabling site {hostname.replace('.','_')}.conf")
    stdin, stdout, stderr = ssh.exec_command(f"a2ensite {hostname.replace('.','_')}.conf")
    print(stderr.read().decode('utf-8'))
    print(f"Restarting apache")
    stdin, stdout, stderr = ssh.exec_command("systemctl reload apache2")
    print(stderr.read().decode('utf-8'))
    ssh.close()

def create_certs(hostname):
    print(f"Creating cert/key for {hostname}")
    ssh = connect_to_server(args.server,args.username,args.password)
    openssl_command = f"""openssl req -nodes -x509 -sha256 -newkey rsa:4096 \
                        -keyout /etc/ssl/private/{hostname}.key \
                        -out  /etc/ssl/certs/{hostname}.crt \
                        -days 356 \
                        -subj "/C=US/ST=Test/L=Seattle/O=Test Corp/OU=IT Dept/CN={hostname}"  \
                        -addext "subjectAltName = DNS:{hostname}" """
    stdin, stdout, stderr = ssh.exec_command(openssl_command)
    ssh.close()
    print(stderr.read().decode('utf-8'))

def main():
    global args
    if sys.version_info < (3, 5):
        print('Please upgrade your Python version to 3.5 or higher')
        sys.exit(1)
    args = usage()   
    parse_HAR(args.har)
    #create_dir_structure()

if __name__ == "__main__":
   main()

