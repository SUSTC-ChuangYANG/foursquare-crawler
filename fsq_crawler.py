import requests
from bs4 import BeautifulSoup
import json 
import argparse 
from tools import load_url_list, save
from tqdm import tqdm
import json 
import yaml 
import datetime
from fake_useragent import UserAgent


class PageNotFoundError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
        
class WrongUrlError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class FoursquareCrawler:
    def __init__(self, proxy="none", debug=False, retry_times=4):
        self.ua = UserAgent(platforms='pc')
        self.reset_status()
        self.debug_mode = debug
        self.proxy = proxy
        self.retry_times = retry_times
        
    def reset_status(self):
        self.success_urls = []
        self.fail_urls = []
        
    def run(self, input_file_path, outdir="none"):
        keyword = "crawl"
        tweet_records  = load_url_list(input_file_path) # 字典列表, 每个字典包含两个字段: URL 和 user_screenname
        input_file_name = input_file_path.split("/")[-1]
        
        self.reset_status()
        print(f"Total number of URLs needed to {keyword}: ", len(tweet_records))
        print(f"Start to {keyword} the checkin metadata of {input_file_name} from the foursquare website...")
        
        self.batch_crawl_fsq_metadata(tweet_records)
        
        print(f"{keyword} is done!")
        print(f"Summary of the {keyword} results:")
        self.summary()
        # 保存成功和失败的数据
        save(crawled_data= self.success_urls, outdir=outdir, outfile_name = input_file_name.replace(".csv", "_successed.csv"), mode="success")
        save(crawled_data = self.fail_urls, outdir=outdir, outfile_name= input_file_name.replace(".csv", "_failed.csv"), mode="failed")
        
    def summary(self):
        print("Success URLs: ", len(self.success_urls))
        print("Fail URLs: ", len(self.fail_urls))
        
    def url_redirect(self, url):
        """从twitter 短链接定向到foursquare的链接"""
        if self.proxy == "none":
            response = requests.get(url, timeout=5)
        else:
            response = requests.get(url, proxies=self.proxy, timeout=5)  # 默认情况下，requests会自动跟随重定向
        final_url = response.url  # 获取最终的Foursquare URL
        if "swarmapp" not in final_url:
            raise WrongUrlError(f"The URL {url} is not a valid foursquare checkin URL.")
        return final_url

    def url_fetch(self, url):
        # 爬取该网页, 获取网页源代码
        agent = self.ua.random
        if self.proxy == "none":
            html = requests.get(url, headers={"User-Agent": agent}, timeout=5)
        else:
            html = requests.get(url, headers={"User-Agent": agent}, proxies=self.proxy, timeout=5) # 伪装成浏览器访问, 随机生成一个header 
        html.encoding = 'utf-8'  # 明确设置响应内容的编码
        # 解析网页
        soup = BeautifulSoup(html.text, "lxml")
        if 'We couldn\'t find the page you\'re looking for.' in soup.text:
            raise PageNotFoundError(f"The URL {url} is deleted or hidden.")
        return soup 

    def content_parse(self, soup):
        """将网页源代码解析成json格式的数据, 包含两个字段: checkin 和 venue
        """
        script_tags = soup.find_all('script', type='text/javascript') # 找到所有的script标签
        for tag in script_tags: 
            if "fourSq.swarm.page.checkin.SwarmCheckinDetail.init" in tag.text: # 找到包含特定字符串的script标签
                fsq_data = {}
                raw_text = tag.text
                data = raw_text.replace("fourSq.swarm.page.checkin.SwarmCheckinDetail.init({el: $('body'),", '')
                # 将字符串 按照 "checkin:" 和 "venue:" 分割
                checkin = data.split("checkin: ")[1].split("venue: ")[0][:-1]
                venue = data.split("venue: ")[1].split("signature: ")[0][:-1]
                parsed_checkin = json.loads(checkin)
                parsed_venue = json.loads(venue)
                fsq_data['checkin'] = parsed_checkin
                fsq_data['venue'] = parsed_venue
                fsq_data['time'] = parsed_checkin['createdAt']
                break
        return fsq_data 

    def checkin_extract(self, parsed_data):

        category_infors = parsed_data["venue"]["categories"]
        category_infors = [ {"id":category_info["id"], "name": category_info["name"], "primary": category_info["primary"]} for category_info in category_infors]
        location_infors = parsed_data["venue"]["location"]
        location_stats = parsed_data["venue"]["stats"]
        name = parsed_data["venue"]["name"]
        uid = parsed_data["checkin"]["user"]["id"]
        fsq_id = parsed_data["venue"]["id"]
        time = datetime.datetime.fromtimestamp(parsed_data["time"]).strftime("%Y-%m-%d %H:%M:%S")

        checkin_metadata = {"fsq_id": fsq_id, "name":name, "time": time,
                        "category": category_infors, "location":location_infors,
                        "uid": uid, "location_stats": location_stats}
        return checkin_metadata



    def get_fsq_metadata(self, tweet_record):
        """url, 提取出签到的元数据, 包括签到的用户id, 性别, 签到的地点id, 名字, 类别, 位置等
        *输出字段介绍*:
        - fsq_id: foursquare的POI地点id, 例如
        - name: POI的名字, e.g., Subway Chikusa Station
        - time: 签到的时间, e.g., '2021-07-01 12:00:00'
        - category: 地点的类别信息
            - category['id']: 类别的id, e.g., '4bf58dd8d48988d1fd931735'
            - category['name']: 类别的名字, e.g., 'Metro Station'
            - category['primary']: 是否是主要类别, e.g., True
        - location: 地点的位置信息
            - location['contextLine']: 上下文信息(地名), e.g., '日本名古屋市'
            - location['country']: 国家, e.g., '日本'
            - location['state']: 都道府县, e.g., '愛知県'
            - location['city']: 城市, e.g., '名古屋市'
            - location['lat']: 纬度, e.g., 35.170653
            - location['lng']: 经度, e.g., 136.929907
            - location['address']: 地址, e.g., '東区葵3-15-21'
            - location['postalCode']: 邮编, e.g., '461-0004'
            - location['cc']: 国家代码, e.g., 'JP'
            - location['neighborhood']: 社区, e.g., '東区', 注意: 有些地点没有这个字段
        - location_stats: 地点的统计信息
            - location_stats['checkinsCount']: 签到次数, e.g., 10523
            - location_stats['usersCount']: 用户数, e.g., 1306
            - location_stats['tipCount']: 提示数, e.g., 3
        - uid: 用户的id, e.g., '1272416'
        - fsq_url: foursquare的网页链接, e.g., 'https://www.swarmapp.com/c/k3miIHJz7DU'
        - tweet_url: twitter的网页链接, e.g., 'https://t.co/Qm5WGMZiGE'
        """
        url, uname = tweet_record["URL"], tweet_record["user_screenname"]
        status_code = 0
        for i in range(self.retry_times): # 重爬机制
            try:
                fs_url = self.url_redirect(url) # step1: 从twitter短链接定向到foursquare的链接 
                raw_html = self.url_fetch(fs_url) # step2: 爬取foursquare的网页 
                parsed_data = self.content_parse(raw_html) # step3: 将网页源代码解析成json格式的数据, 包含两个字段: checkin 和 venue
                checkin_metadata = self.checkin_extract(parsed_data) # step4: 提取出签到的元数据 
                # step5: 添加foursquare和twitter的网页链接, 以及用户的screenname
                checkin_metadata['fsq_url'] = fs_url 
                checkin_metadata['tweet_url'] = url 
                checkin_metadata['user_screenname'] = uname
                # step6: 存储到缓冲区 success_urls 中
                self.success_urls.append(checkin_metadata)
                status_code = 1 # 成功爬取
                if i != 0: # 如果不是一次成功, 则打印重爬的次数
                    print("[Try-{}] Successfully to extract metadata from the checkin URL: {}".format(i, url))
                break
            except PageNotFoundError as e:
                print("Error: ", e)
                status_code = 2 # 未找到页面
                tweet_record["reason"] = "PageNotFound"
                self.fail_urls.append(tweet_record)
                break
            except WrongUrlError as e:
                print("Error: ", e)
                status_code = 3 # 错误的URL
                tweet_record["reason"] = "WrongUrl"
                self.fail_urls.append(tweet_record)
                break
            except Exception as e:
                status_code = 0 # 未知错误
                print("Error: ", e)
                print("[Try-{}] Failed to extract metadata from the checkin URL: {}".format(i, url))
                continue
            
        if status_code == 0:
            print("Max retry times reached, failed to extract metadata from the checkin URL: {}".format(url))   
            tweet_record["reason"] = "MaxRetry"
            self.fail_urls.append(tweet_record)
        
        
        if self.debug_mode:
            if status_code == 1:
                print("Success to extract metadata from the checkin URL: {}".format(url))
                print(json.dumps(checkin_metadata,ensure_ascii=False, indent=4))
            
    def batch_crawl_fsq_metadata(self, tweet_records):
        for record in tqdm(tweet_records):
            self.get_fsq_metadata(record)

def get_proxy(ip_pool="pool_1"):
    with open('ip_pool.yaml', 'r') as file:
        config = yaml.safe_load(file)
        pool_name = config[ip_pool]['poolname']
        host = config[ip_pool]['host']
        username = config[ip_pool]['username']
        password = config[ip_pool]['password']
        return {'http': f'http://{username}:{password}@{host}', 'https': f'http://{username}:{password}@{host}'}
            

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default="none", help="The file path of the target URLs")
    parser.add_argument("--ip_pool", type=str, default="none", help="The file path of the IP pool")
    parser.add_argument("--outdir", type=str, default="none", help="The output directory of the crawled data")
    parser.add_argument("--mode", type=str, default="batch", help="The mode of the crawler, batch or debug")
    parser.add_argument('--url', type=str, default="none", help="The URL of the target foursquare checkin, only used in debug mode")
    parser.add_argument('--retry_times', type=int, default=4, help="The retry times of the crawler")
    
    print("*"*50)
    args = parser.parse_args()
    if args.ip_pool != "none":
        proxy = get_proxy(args.ip_pool)
        print("Proxy is used.")
    else:
        proxy = "none"
        print("Proxy is not used.")

    # -------------------debug mode ------------------------        
    if args.mode == 'debug':
        print("Debug mode is enabled.")
        fsq_crawler = FoursquareCrawler(proxy=proxy, debug=True, retry_times=args.retry_times)
        fsq_crawler.get_fsq_metadata({"URL":args.url, "user_screenname": "test_user"})
    # -------------------batch mode ------------------------       
    elif args.mode == "batch":
        print("Batch mode is enabled.")
        if args.file == "none" or args.outdir == "none":
            print("Please specify the file path and output directory.")
            exit()
        fsq_crawler = FoursquareCrawler(proxy=proxy, debug=False, retry_times=args.retry_times)
        fsq_crawler.run(input_file_path=args.file, outdir=args.outdir)
        print(args.file, "done!")