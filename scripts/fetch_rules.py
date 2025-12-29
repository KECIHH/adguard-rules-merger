#!/usr/bin/env python3
"""
规则抓取器 v4.2 (GitHub Actions 优化版)
优化：连接池、流式处理、内存优化
"""

import os
import sys
import time
import shutil
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

TEMP_DIR = "temp"
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 30
MAX_WORKERS = min(16, (os.cpu_count() or 2) * 2)
CHUNK_SIZE = 64 * 1024  # 64KB
MAX_RETRIES = 3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

class Downloader:
    def __init__(self):
        self.session = requests.Session()
        # GitHub Actions 友好 User-Agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; AdBlockRulesFetcher/4.2; +https://github.com)'
        })
        
        # 优化连接池
        adapter = HTTPAdapter(
            pool_connections=MAX_WORKERS,
            pool_maxsize=MAX_WORKERS,
            max_retries=Retry(
                total=MAX_RETRIES,
                backoff_factor=0.5,
                status_forcelist=[500, 502, 503, 504]
            )
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def get_filename(self, idx, domain):
        """生成安全的文件名"""
        safe_domain = "".join(c if c.isalnum() or c in '.-_' else '_' for c in domain)
        safe_domain = safe_domain[:50]
        return f"{TEMP_DIR}/{idx:04d}_{safe_domain}.txt"
    
    def count_rules_streaming(self, file_path):
        """流式统计规则行数，内存友好"""
        count = 0
        try:
            with open(file_path, 'rb') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith(b'!'):
                        count += 1
        except Exception as e:
            logging.error(f"统计规则时出错: {e}")
        return count
    
    def download_source(self, idx, url, domain, name):
        """下载单个规则源"""
        output_file = self.get_filename(idx, domain)
        temp_file = f"{output_file}.tmp"
        
        try:
            logging.debug(f"开始下载: {domain}")
            
            response = self.session.get(
                url, 
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                stream=True
            )
            response.raise_for_status()
            
            # 检查内容类型
            content_type = response.headers.get('content-type', '').lower()
            if 'text' not in content_type and 'octet-stream' not in content_type:
                logging.warning(f"{domain}: 非文本内容类型: {content_type}")
            
            # 流式下载到临时文件
            total_size = 0
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)
            
            # 验证文件
            if total_size < 10:
                raise ValueError(f"文件太小 ({total_size} bytes)")
            
            # 统计规则（流式，避免内存问题）
            rule_count = self.count_rules_streaming(temp_file)
            
            # 重命名文件
            os.replace(temp_file, output_file)
            
            logging.info(f"{domain:<30} {rule_count:>8} 条规则  {total_size/1024:>8.1f} KB")
            return rule_count, total_size
            
        except Exception as e:
            logging.error(f"{domain}: 下载失败: {e}")
            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return None

def read_sources(path="sources/sources.txt"):
    """读取规则源列表"""
    sources = []
    seen = set()
    
    if not os.path.exists(path):
        logging.error(f"源文件不存在: {path}")
        sys.exit(1)
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 移除行内注释
                url = line.split('#')[0].strip()
                if not url.startswith(('http://', 'https://')):
                    logging.warning(f"第{line_num}行: 跳过非HTTP URL")
                    continue
                
                if url in seen:
                    continue
                
                seen.add(url)
                
                try:
                    parsed = urlparse(url)
                    domain = parsed.netloc
                    if not domain:
                        raise ValueError("无法解析域名")
                    
                    sources.append((url, domain, domain.replace('.', '_')))
                    
                except Exception as e:
                    logging.error(f"第{line_num}行: URL解析失败: {e}")
    except Exception as e:
        logging.error(f"读取源文件失败: {e}")
        sys.exit(1)
    
    logging.info(f"读取到 {len(sources)} 个规则源")
    return sources

def main():
    """主函数"""
    start_time = time.time()
    
    # 清理临时目录
    temp_path = Path(TEMP_DIR)
    if temp_path.exists():
        shutil.rmtree(TEMP_DIR)
    temp_path.mkdir(exist_ok=True)
    
    # 读取规则源
    sources = read_sources()
    if not sources:
        logging.error("没有找到有效的规则源")
        return
    
    # 初始化下载器
    downloader = Downloader()
    total_rules = 0
    total_size = 0
    failed_sources = []
    
    # 并行下载
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_domain = {}
        
        for i, (url, domain, name) in enumerate(sources, 1):
            future = executor.submit(
                downloader.download_source, i, url, domain, name
            )
            future_to_domain[future] = domain
        
        # 处理结果
        for future in as_completed(future_to_domain):
            domain = future_to_domain[future]
            try:
                result = future.result()
                if result:
                    rules, size = result
                    total_rules += rules
                    total_size += size
                else:
                    failed_sources.append(domain)
            except Exception as e:
                logging.error(f"{domain}: 任务异常: {e}")
                failed_sources.append(domain)
    
    # 输出统计
    logging.info("=" * 60)
    logging.info(f"总计规则: {total_rules:,} 条")
    logging.info(f"总计大小: {total_size/1024/1024:.2f} MB")
    logging.info(f"成功: {len(sources) - len(failed_sources)}/{len(sources)}")
    
    if failed_sources:
        logging.warning(f"失败的源: {', '.join(failed_sources[:10])}{'...' if len(failed_sources) > 10 else ''}")
        with open(f"{TEMP_DIR}/failed_sources.txt", 'w', encoding='utf-8') as f:
            f.write('\n'.join(failed_sources))
    
    elapsed = time.time() - start_time
    logging.info(f"总耗时: {elapsed:.1f}秒")

if __name__ == "__main__":
    main()