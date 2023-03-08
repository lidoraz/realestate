cd resources
path="https://real-estate-public.s3.eu-west-2.amazonaws.com/resources"
wget $path/yad2_rent_df.pk
wget $path/yad2_forsale_df.pk
wget $path/yad2_rent_df.pk
cd ..

export PYTHONPATH=.;
python app_map/dashboard_yad2_forsale.py