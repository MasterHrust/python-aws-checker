import speedtest
from pythonping import ping
import folium
from folium.plugins import MarkerCluster
import requests

def measure_latency():
    # Измеряем задержку до локального хоста
    st = speedtest.Speedtest()
    st.get_best_server()
    local_latency = st.results.ping

    # Измеряем задержку до регионов AWS
    regions = [
        'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
        'af-south-1', 'ap-east-1', 'ap-south-1', 'ap-northeast-1',
        'ap-northeast-2', 'ap-northeast-3', 'ap-southeast-1', 'ap-southeast-2',
        'ca-central-1', 'eu-central-1', 'eu-west-1', 'eu-west-2',
        'eu-west-3', 'eu-north-1', 'me-south-1', 'sa-east-1'
    ]

    latencies = {}
    for region in regions:
        try:
            response_list = ping(f"ec2.{region}.amazonaws.com", count=3, size=56)
            latency = round(response_list.rtt_avg_ms, 2)
            latencies[region] = latency
        except Exception as e:
            print(f"Failed to measure latency for region {region}: {str(e)}")

    return local_latency, latencies

def build_map(local_latency, latencies, user_location):
    # Создаем карту с отображением регионов AWS
    aws_map = folium.Map(location=user_location, zoom_start=3)

    # Добавляем маркер для локальной задержки
    folium.Marker(
        location=user_location,
        popup=f"Your Location\nLocal Latency: {local_latency} ms",
        icon=folium.Icon(color='blue', icon_anchor=[10,10])
    ).add_to(aws_map)

    # Отображаем регионы
    min_latency = min(latencies.values())
    max_latency = max(latencies.values())
    for region, latency in latencies.items():
        location = get_region_coordinates(region)
        color = 'green' if latency == min_latency else 'red' if latency == max_latency else 'black'
        folium.Marker(
            location=location,
            popup=f"{region}\nLatency: {latency} ms",
            icon=folium.Icon(
                color=color,
            )
        ).add_to(aws_map)
        # Соединяем регион с пользователем
        points = [user_location, location]
        folium.PolyLine(points, color="red", weight=1, opacity=0.5).add_to(aws_map)

    # Добавляем выделение регионов
    min_latency_region = min(latencies, key=latencies.get)
    max_latency_region = max(latencies, key=latencies.get)
    folium.Marker(
        location=get_region_coordinates(min_latency_region),
        popup=f"Region: {min_latency_region}\nLatency: {latencies[min_latency_region]} ms (Minimum)",
        icon=folium.Icon(color='green')
    ).add_to(aws_map)

    folium.Marker(
        location=get_region_coordinates(max_latency_region),
        popup=f"Region: {max_latency_region}\nLatency: {latencies[max_latency_region]} ms (Maximum)",
        icon=folium.Icon(color='red')
    ).add_to(aws_map)

    # Создаем таблицу с регионами и пингом
    html_content = f"""
    <html>
    <head></head>
    <body>
    <h2>Latency Table</h2>
    <button onclick="toggleTable()">Toggle Latency Table</button>
    <div id="latency_table" style="display: none">
    <table border="1" cellspacing="0" cellpadding="5">
      <tr>
        <th>Region</th>
        <th>Latency (ms)</th>
      </tr>
    """
    for region, latency in latencies.items():
        color = 'green' if latency == min_latency else 'red' if latency == max_latency else 'black'
        html_content += f"<tr style='color: {color}'><td>{region}</td><td>{latency}</td></tr>"
    html_content += """
    </table>
    </div>
    """

    # Добавляем карту в HTML
    html_content += """<h2>AWS Latency Map</h2>"""
    aws_map.save('aws_latency_map_v2.html')
    with open('aws_latency_map_v2.html', 'r') as file:
        map_html = file.read()
        html_content += map_html

    html_content += """
    <script>
    function toggleTable() {
      var x = document.getElementById("latency_table");
      if (x.style.display === "none") {
        x.style.display = "block";
      } else {
        x.style.display = "none";
      }
    }
    </script>
    </body>
    </html>
    """

    # Создаем общий HTML файл
    with open("aws_latency_v2.html", "w") as file:
        file.write(html_content)

    print("Map created successfully!")

def get_region_coordinates(region_name):
    # Координаты регионов AWS для отображения на карте
    region_coordinates = {
        'us-east-1': (39.833333, -98.585522),
        'us-east-2': (39.833333, -75.5),
        'us-west-1': (37.833333, -119.5),
        'us-west-2': (45.5, -122.5),
        'af-south-1': (-30, 26),
        'ap-east-1': (22.3193039, 114.1693611),
        'ap-south-1': (19.0760, 72.8777),
        'ap-northeast-1': (35.6895, 139.6917),
        'ap-northeast-2': (37.5665, 126.9780),
        'ap-northeast-3': (35.6895, 139.6917),
        'ap-southeast-1': (1.3521, 103.8198),
        'ap-southeast-2': (-33.8688, 151.2093),
        'ca-central-1': (45.4215, -75.6919),
        'eu-central-1': (50.1109, 8.6821),
        'eu-west-1': (51.5074, -0.1278),
        'eu-west-2': (53.3498, -2.5879),
        'eu-west-3': (48.8566, 2.3522),
        'eu-north-1': (59.3293, 18.0686),
        'me-south-1': (25.276987, 55.296249),
        'sa-east-1': (-23.5505, -46.6333)
    }
    return region_coordinates.get(region_name, (0, 0))

def get_user_location():
    response = requests.get('https://ipinfo.io')
    data = response.json()
    loc = data['loc'].split(',')
    return list(map(float, loc))

def main():
    local_latency, latencies = measure_latency()
    print(f"Local latency: {local_latency} ms")
    print("Latencies to AWS regions:")
    for region, latency in latencies.items():
        print(f"{region}: {latency} ms")

    # Определение локации пользователя
    user_location = get_user_location()
    build_map(local_latency, latencies, user_location)

if __name__ == "__main__":
    main()
