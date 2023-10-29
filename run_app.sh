#cd resources
#path="https://real-estate-public.s3.eu-west-2.amazonaws.com/resources"
#wget $path/yad2_rent_df.pk
#wget $path/yad2_forsale_df.pk
#wget $path/df_nadlan_recent.pk.pk
#cd ..
#

#https://real-estate-public.s3.eu-west-2.amazonaws.com/resources/df_nadlan_recent.pk
export PYTHONPATH=.;
python app_map/app.py prod
#python app_map/dashboard_yad2_forsale.py prod

### install python3.11 in yum amazon
sudo yum install gcc openssl-devel bzip2-devel libffi-devel zlib-devel -y

sudo yum groupinstall "Development Tools"
sudo yum install libffi-devel bzip2-devel
sudo yum uninstall openssl-devel
sudo yum install openssl11-devel


# # https://dev.to/hkamran/installing-a-newer-version-of-python-on-amazon-ec2-1b4n
wget https://www.python.org/ftp/python/3.11.6/Python-3.11.6.tgz
tar xzf Python-3.11.6.tgz
cd Python-3.11.6
sudo ./configure --enable-optimizations
sudo make altinstall
sudo rm -f /opt/Python-3.11.6.tgz
cd ..
sudo rm -r Python-3.11.6
# pip3.11 install XXXX
# XXXpython3.11


alias python3='python3.11'
