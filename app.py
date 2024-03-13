import requests
from flask import Flask, render_template, request

app = Flask(__name__)

# 高德地图API的Key，请替换成你的实际Key
api_key = "9afa649960a68767bd3906977934d59b"


def get_location_by_keyword(keyword, city):
    """根据关键字查询地点经纬度"""
    url = f"https://restapi.amap.com/v3/place/text?key={api_key}&keywords={keyword}&city={city}&types=&children=1&offset=1&page=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data["pois"]:
            location = data["pois"][0]["location"]
            return location
    return None


def get_transit_path_plan(origin, destination, city):
    url = f"https://restapi.amap.com/v3/direction/transit/integrated?key={api_key}&origin={origin}&destination={destination}&city={city}&extensions=all"
    response = requests.get(url)
    detailed_steps = []
    if response.status_code == 200:
        data = response.json()
        if data.get("route") and data["route"].get("transits"):
            transits = data["route"]["transits"]
            for transit in transits[:1]:  # 以第一个选项作为示例
                for segment in transit.get("segments", []):
                    # 处理步行信息
                    walking = segment.get("walking")
                    if walking and walking.get('steps'):
                        for step in walking['steps']:
                            instruction = step.get('instruction')
                            if instruction:
                                detailed_steps.append(f"步行说明: {instruction}")

                    # 处理公交信息
                    bus = segment.get("bus")
                    if bus and bus.get("buslines"):
                        for busline in bus.get("buslines", [])[:1]:  # 以第一条公交线路作为示例
                            name = busline.get('name')
                            departure_stop = busline.get('departure_stop', {}).get('name')
                            arrival_stop = busline.get('arrival_stop', {}).get('name')
                            if name and departure_stop and arrival_stop:
                                detailed_steps.append(f"乘坐公交{busline['name']}, 从{departure_stop}到{arrival_stop}")

                    # 处理地铁信息
                    railway = segment.get("railway")
                    if railway:
                        name = railway.get('name')
                        departure_stop = railway.get('departure_stop', {}).get('name')
                        arrival_stop = railway.get('arrival_stop', {}).get('name')
                        if name and departure_stop and arrival_stop:
                            detailed_steps.append(f"乘坐地铁{railway['name']}, 从{departure_stop}到{arrival_stop}")
    return detailed_steps


def find_optimal_route(start_keyword, destination_keywords, city):
    """根据给定的起点和一系列目的地，计算并返回详细的路径规划信息。"""
    # 先获取起点的位置
    start_location = get_location_by_keyword(start_keyword, city)
    if not start_location:
        return {"error": "起点位置信息获取失败"}

    detailed_routes = []
    current_location = start_location
    current_keyword = start_keyword

    # 依次处理每个目的地
    for destination_keyword in destination_keywords:
        destination_location = get_location_by_keyword(destination_keyword, city)
        if not destination_location:
            continue  # 如果无法获取目的地的位置信息，则跳过

        detailed_steps = get_transit_path_plan(current_location, destination_location, city)
        detailed_routes.append({
            "from": current_keyword,
            "to": destination_keyword,
            "steps": detailed_steps
        })

        # 更新当前位置和关键词，为下一次迭代准备
        current_location = destination_location
        current_keyword = destination_keyword

    return detailed_routes


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        start_keyword = request.form.get('start_name')
        destinations_input = request.form.get('destinations')
        destination_keywords = [name.strip() for name in destinations_input.split(',')]
        city = request.form.get('city', '北京')

        detailed_routes = find_optimal_route(start_keyword, destination_keywords, city)
        return render_template('result.html', detailed_routes=detailed_routes, start_keyword=start_keyword,
                               destination_keywords=destination_keywords)
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    start_keyword = request.form.get('start_name')
    destinations_input = request.form.get('destinations')
    destination_keywords = [name.strip() for name in destinations_input.split(',')]
    city = request.form.get('city', '北京')

    detailed_routes = find_optimal_route(start_keyword, destination_keywords, city)
    return render_template('result.html', detailed_routes=detailed_routes, start_keyword=start_keyword,
                           destination_keywords=destination_keywords)


if __name__ == '__main__':
    app.run(debug=True)
