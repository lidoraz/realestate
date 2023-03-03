import requests


def _get_parse_item_add_info(item_id):
    yad2_url_item = "https://gw.yad2.co.il/feed-search-legacy/item?token={}"
    try:
        d = requests.get(yad2_url_item.format(item_id)).json()['data']
        is_bad = d.get('error_message') is not None
        if is_bad:
            return None
        items_v2 = {x['key']: x['value'] for x in d['additional_info_items_v2']}
        add_info = dict(id=item_id,
                        parking=0 if d['parking'] == "ללא" else int(d['parking']),
                        balconies=True if d['balconies'] else False,
                        number_of_floors=d['TotalFloor_text'],
                        renovated=items_v2.get('renovated'),
                        asset_exclusive_declaration=items_v2.get('asset_exclusive_declaration'),
                        air_conditioner=items_v2.get('air_conditioner'),
                        bars=items_v2.get('bars'),
                        elevator=items_v2.get('elevator'),
                        boiler=items_v2.get('boiler'),
                        accessibility=items_v2.get('accessibility'),
                        shelter=items_v2.get('shelter'),
                        warhouse=items_v2.get('warhouse'),
                        tadiran_c=items_v2.get('tadiran_c'),
                        furniture=items_v2.get('furniture'),
                        flexible_enter_date=items_v2.get('flexible_enter_date'),
                        kosher_kitchen=items_v2.get('kosher_kitchen'),
                        housing_unit=items_v2.get('housing_unit'),
                        square_meters=d.get('square_meters'),
                        square_meter_build=d.get('square_meter_build'),
                        garden_area=d.get('garden_area'),
                        info_text=d['info_text'],
                        image_urls=d['images_urls']
                        )
        return add_info
    except Exception as e:
        print(f"Failed to fetch for {item_id}")
    return None
