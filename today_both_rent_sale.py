import requests
import pandas as pd
import os

LIMIT = 100

print("Generating today rent sale")
url = f"{os.environ['REAL_ESTATE_API']}/today_both_rent_sale"

style = """
        * {font-family: sans-serif;}
        h1 {
        text-align: center;
        }
        .main-cont{
        margin: 50px;
        }
        table {
        border-collapse: collapse;
        width: 100%;
        font-size: 11pt;
        }
        .col_heading {
        background: antiquewhite;
        /*padding: 0px 5px 0px;*/
        }
        .cont-img {
        height: 150px;
        width: 180px;
        background: white;
        display: flex;
        align-items: center;
        padding: 10px;
        }

        .ticker-img {
        max-height: 150px;
        max-width: 180px;
        }
        .zoom {
          transition: transform .2s; /* Animation */
          margin: 0 auto;
        }
        
        .zoom:hover {
          transform: scale(2.0); /* (150% zoom - Note: if the zoom is too large, it will go outside of the viewport) */
        }
        table.dataTable thead th, table.dataTable thead td {
          padding: 3px 6px; !important
        }
        table.dataTable tbody th, table.dataTable tbody td{
            padding: 3px 6px; !important
        }
        #T_stocks thead th{
          position: sticky;
          top: 0;
          background-color: white;
          background-repeat: no-repeat;
        }
        #T_stocks_filter{
            float: left;
        }
        a {
          color: inherit; /* blue colors for links too */
          text-decoration: inherit; /* no underline */
        }
    """

results = requests.post(url, json={"limit": LIMIT}).json()
df = pd.DataFrame(results['data_today_both_rent_sale'])
default_img = "https://ateamymm.ca/defaulthouse.jpg"
df["sale_img"] = df["sale_img"].replace("", default_img)
df["rent_img"] = df["rent_img"].replace("", default_img)
df["sale_added"] = pd.to_datetime(df["sale_added"]).dt.date
df["rent_added"] = pd.to_datetime(df["rent_added"]).dt.date
df["yearly_pct"] = df["yearly_pct"] / 100
img_ticker_s = '<div class="cont-img"><a href="{}" target="blank"> <img src="{}" loading="lazy" class="ticker-img zoom" /></a></div>'
df['SALE'] = df.apply(lambda row: img_ticker_s.format(row['sale_link'], row['sale_img']), axis=1)
df['RENT'] = df.apply(lambda row: img_ticker_s.format(row['rent_link'], row['rent_img']), axis=1)
frmts = {"sale_price": '₪{:,.0f}', "rent_price": '₪{:,.0f}', "yearly_pct": "{:.2%}", "rooms": "{:.1f}"}
columns = ['SALE', 'RENT', 'city', 'sale_price', 'rent_price', "street_num",
           'yearly_pct', 'asset_type', 'rooms',
           'floor', 'neighborhood', 'asset_status', 'sale_added', 'rent_added']

df = df[columns]
out_df = df.style.format(frmts)
out_df = out_df.to_html(table_uuid="deals")
str_html = f"""
        <html><head>
        <title>Today Rent Sale</title>
        <link rel="icon" type="image/x-icon" href="favicon.ico">
        <link href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css" rel="stylesheet">
        <style>
        {style}
        </style>
        </head><body>
        <div class="main-cont">
        <h1>Today Rent Sale, Click on the image to view</h1>
        <script src="https://code.jquery.com/jquery-3.6.0.slim.min.js" integrity="sha256-u7e5khyithlIdTpu22PHhENmPcRdFiHRjhAuHcs05RI=" crossorigin="anonymous"></script>
        <script type="text/javascript" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
        {out_df}
        <script>
            $(document).ready( function () {{
                $('#T_sectors').DataTable({{
                    searching: false,
                    info: false,
                    fixedHeader: true, // not working, fixed with sticky header
                    paging: false,   
                    order: [[yearly, 'desc']],
                    // scrollY: 400,
                }});
            }});
        </script>
        </body>
        </html>
"""

with open("real_eastate_deals.html", 'w', encoding="utf-8") as f:
    f.write(str_html)
