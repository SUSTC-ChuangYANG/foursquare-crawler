import pandas as pd
import os 

def flatten_dict(d, parent_key='', sep='_'):
    """
    Flatten a multi-level nested dictionary into a single-level dictionary
    :param d: original dictionary
    :param parent_key: the upper level key used to construct new keys
    :param sep: character for connecting the upper level key and the current key
    :return: flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f'{parent_key}{sep}{k}' if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def load_url_list(file_path):
    url_df = pd.read_csv(file_path)
    url_list = url_df['URL'].tolist()
    uname_list = url_df['user_screenname'].tolist()
    records = []
    for url, uname in zip(url_list, uname_list):
        records.append({"URL": url, "user_screenname": uname})
    print("*"*50)
    return records

def save(crawled_data, outdir, outfile_name, mode="success"):
    # Check if the output directory exists, and create it if it does not.
    if not os.path.exists(outdir):
        os.makedirs(outdir)
        
    output_file_path = os.path.join(outdir, outfile_name)
    if len(crawled_data) != 0:
        crawled_data = [flatten_dict(d) for d in crawled_data]
        if mode == "success": 
            for d in crawled_data:
                d["uid"] = "uid_"+str(d["uid"]) # 为uid添加前缀, 避免uid被解析为科学计数法
            df = pd.DataFrame(crawled_data)
            df.to_csv(output_file_path, index=False)
        else:
            df = pd.DataFrame(crawled_data)
            df.to_csv(output_file_path, index=False)
        
