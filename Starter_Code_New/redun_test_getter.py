import requests
import json
import time
from datetime import datetime
import csv
import os

# --- 配置项 ---
BASE_URL = "http://localhost"
START_DASHBOARD_PORT = 8000  # 第一个 peer 的 dashboard 映射端口
END_DASHBOARD_PORT = 8010    # 最后一个 peer 的 dashboard 映射端口
API_ENDPOINT = "/redundancy" # API 路径
SCRAPE_INTERVAL_SECONDS = 600 # 爬取间隔，10 分钟 = 600 秒
OUTPUT_FILE = "redundancy_data.csv" # 数据保存的 CSV 文件名
REQUEST_TIMEOUT = 5 # 请求超时时间（秒）

def get_peer_ids_and_urls():
    """
    根据 docker-compose.yml 的端口映射规则，生成 (peer_id, url) 元组列表。
    例如：8000 -> peer5000, 8001 -> peer5001
    """
    peers_info = []
    for port in range(START_DASHBOARD_PORT, END_DASHBOARD_PORT + 1):
        # peer_id = 映射端口 - 3000 (例如 8000 - 3000 = 5000)
        peer_id = port - 3000
        url = f"{BASE_URL}:{port}{API_ENDPOINT}"
        peers_info.append((peer_id, url))
    return peers_info

def determine_csv_header(peers_info):
    """
    尝试从第一个成功的 API 响应中获取数据键，以确定 CSV 文件的列头。
    """
    print("尝试从示例 peer 获取数据以确定 CSV 列头...")
    for peer_id, url in peers_info:
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status() # 对 4xx/5xx 状态码抛出 HTTPError
            data = response.json()
            
            if isinstance(data, dict):
                print(f"从 {url} 获取到示例数据 (字典): {data}")
                return list(data.keys())
            elif isinstance(data, (int, float)):
                print(f"从 {url} 获取到示例数据 (数字): {data}")
                return ["value"] # 如果 API 返回的是单个数字，使用 'value' 作为列名
            else:
                print(f"警告: 从 {url} 获取到的示例数据格式非字典或数字: {data}。尝试下一个 peer。")
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"警告: 无法从 {url} 获取示例数据: {e}。尝试下一个 peer。")
        except Exception as e:
            print(f"确定列头时发生意外错误 ({url}): {e}。尝试下一个 peer。")
            
    print("未能从任何 peer 确定列头。使用默认列头 ['redundant_count']。")
    return ["redundant_count"] # 最终的备用列头

def scrape_data(peers_info, csv_data_keys):
    """
    爬取所有 peer 的冗余数据并保存到 CSV 文件。
    """
    current_time = datetime.now()
    print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] 开始数据爬取...")

    file_exists = os.path.exists(OUTPUT_FILE)
    
    with open(OUTPUT_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # 如果文件不存在，则写入 CSV 列头
        if not file_exists:
            full_header = ["timestamp", "peer_id"] + csv_data_keys
            writer.writerow(full_header)
            print(f"CSV 列头已写入: {full_header}")

        current_timestamp_iso = current_time.isoformat()

        for peer_id, url in peers_info:
            try:
                response = requests.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status() # 检查 HTTP 错误
                data = response.json()
                
                row_data = [current_timestamp_iso, peer_id]
                
                if isinstance(data, dict):
                    for key in csv_data_keys:
                        # 使用 .get() 方法，如果某个键不存在，则返回 None
                        row_data.append(data.get(key)) 
                elif isinstance(data, (int, float)):
                    # 如果 API 返回的是单个数字，将其添加到行数据中
                    row_data.append(data)
                    # 如果预期的列头多于一个（例如，如果最初是字典，后来变成数字），
                    # 则用 None 填充剩余的列
                    for _ in range(len(csv_data_keys) - 1):
                        row_data.append(None)
                else:
                    print(f"警告: 从 {url} 获取到的数据格式异常: {data}。跳过此 peer 的数据。")
                    continue

                writer.writerow(row_data)
                print(f"  已爬取 {url}: {data}")

            except requests.exceptions.ConnectionError as e:
                print(f"  连接 {url} 失败: {e}")
            except requests.exceptions.Timeout as e:
                print(f"  连接 {url} 超时: {e}")
            except requests.exceptions.HTTPError as e:
                print(f"  HTTP 错误从 {url}: {e}")
            except json.JSONDecodeError as e:
                print(f"  从 {url} 解析 JSON 失败: {e}。响应内容: {response.text[:100]}...")
            except Exception as e:
                print(f"  {url} 发生意外错误: {e}")
    
    print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] 数据爬取完成。休眠 {SCRAPE_INTERVAL_SECONDS} 秒...")

def main():
    peers_info = get_peer_ids_and_urls()
    
    # 在程序启动时确定 CSV 列头，假设 API 返回的数据结构在运行时是稳定的
    csv_data_keys = determine_csv_header(peers_info)

    print(f"数据将保存到文件: {OUTPUT_FILE}")
    print(f"爬取将每 {SCRAPE_INTERVAL_SECONDS / 60} 分钟进行一次。")
    
    while True:
        scrape_data(peers_info, csv_data_keys)
        time.sleep(SCRAPE_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()