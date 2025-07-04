from logging import config
import os
import yaml

MAIN_GROUP = '🚀 节点选择'

SPECIAL_TAG = ['REJECT', 'DIRECT']

DNS = {
    "enable": True,  # 启用 DNS 功能
    "ipv6": False,  # 禁用 IPv6，减少潜在的解析问题
    "listen": "0.0.0.0:1053",  # 监听地址和端口
    "prefer-h3": True,  # 优先使用 DoH3
    "respect-rules": True,  # 遵循 Clash 路由规则
    "enhanced-mode": "fake-ip",  # 使用增强模式
    "cache-algorithm": "arc",  # 使用 ARC 缓存算法
    "cache-size": 2048,  # 缓存大小
    "use-hosts": False,  # 不使用自定义 hosts
    "use-system-hosts": False,  # 不使用系统 hosts
    "fake-ip-range": "198.18.0.1/16",  # fake-ip 范围
    "fake-ip-filter-mode": "blacklist",
    "fake-ip-filter": [
        "geosite:connectivity-check",
        "geosite:private",
        "*"
    ],
    "default-nameserver": [
        "223.5.5.5",  # 阿里
        "119.29.29.29",  # 腾讯
        "system"
    ],
    "proxy-server-nameserver": [
        'https://doh.pub/dns-query', 
        'https://dns.alidns.com/dns-query'
    ],
    "nameserver": [
        "https://1.1.1.1/dns-query",  # Cloudflare DoH3
        "https://dns.google/dns-query",  # Google DoH3
        "https://dns.alidns.com/dns-query",  # 阿里
        "https://doh.pub/dns-query"  # 腾讯
    ],
    "nameserver-policy": {
        "geosite:cn,private": [
            "https://223.5.5.5/dns-query",
            "https://doh.pub/dns-query"
        ],
        "geo:cn": [
            "https://223.5.5.5/dns-query"
        ]
    },
    "fallback": [
        "1.1.1.1",
        "8.8.8.8"
        # "9.9.9.9"  # Quad9 可选
    ]
}

class FlowStyleList(list):
    pass

def represent_flow_style_list(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)

yaml.add_representer(FlowStyleList, represent_flow_style_list)

class ConfigProcessor:
    def __init__(self, interval=300, lb_strategy='sticky-sessions'):
        self.rules = []
        self.proxy_groups_name = []
        self.config_group_details = []
        self.proxy_groups = []
        self.fallback_groups = []
        self.main_servers = []
        self.fallback_servers = []
        self.interval = interval
        self.lb_strategy = lb_strategy
        self.health_check = {
            'url': 'http://www.qq.com/',
            'interval': interval,
            'timeout': 1000
        }
        pass

    def _list_folder_files(self, folder_path):
        """
        List all files in the specified folder.
        :param folder_path: Path to the folder.
        :return: List of file names in the folder.
        """
        files = [
            f for f in os.listdir(f'./{folder_path}')
            if os.path.isfile(os.path.join(f'./{folder_path}', f)) and f.endswith('.yaml')
        ]
        return sorted(files)

    def _load_yaml(self, file_path):
        """
        Load a YAML file and return its content.
        :param file_path: Path to the YAML file.
        :return: Parsed YAML content.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
        
    def _load_servers(self, servers_type='main_servers'):
        concate_servers = []
        server_files = self._list_folder_files(servers_type)

        for filename in server_files:
            file_servers = []
            file = filename.replace('.yaml', '')
            # Load YAML data
            data = self._load_yaml(os.path.join(f'./{servers_type}', filename))
            servers = data.get('proxies', [])
            for server in servers:
                if any(keyword in server.get('name', '') for keyword in ['帐户', '账户', '余', '官网', '域名', '下次']):
                    continue
                file_servers.append(server)
            # Add the file name as a prefix to the server name
            if file_servers != []:
                for server in file_servers:
                    server['name'] = file + ' | ' + server.get('name', '')
            concate_servers.extend(file_servers)

        return concate_servers


    def _rules_process(self, group_name, rules):
        for rule in rules:
            if not rule.endswith('no-resolve'):
                new_rule = rule+','+group_name
            else:
                new_rule = rule.replace('no-resolve', f'{group_name},no-resolve')
            if new_rule not in self.rules:
                self.rules.append(new_rule)

    def read_rules(self):
        rule_list = self._list_folder_files('rules')
        self.config_group_details = []

        for rule_file in rule_list:
            data = self._load_yaml(os.path.join('./rules', rule_file))
            group_name = data['group_name']
            key_word = data.get('key_word', [])
            rules = data['rules']
            rule_type = data.get('type', 'select')
            fallback_enabled = data.get('fallback_enabled', False)
            fallback_group = data.get('fallback_group', [])
            self._rules_process(group_name, rules)
            self.proxy_groups_name.append(group_name)

            self.config_group_details.append({
                'name': group_name,
                'key_word': key_word,
                'type': rule_type,
                'fallback_enabled': fallback_enabled,
                'fallback_group': fallback_group
            })

    def _create_main_group(self):
        proxies = self.proxy_groups_name
        proxies.remove(MAIN_GROUP)
        proxies.extend(['DIRECT', 'REJECT'])
        main_server_names = [server.get('name', '') for server in self.main_servers]
        proxies.extend(main_server_names)
        fallback_server_names = [server.get('name', '') for server in self.fallback_servers]
        proxies.extend(fallback_server_names)

        self.proxy_groups.append({
            'name': MAIN_GROUP,
            'type': 'select',
            'proxies': proxies,
        })

    def _create_fallback_group(self, group):
        group_name = group['name']
        key_word = group['key_word']
        server_include = [group_name+' LB']

        # Add fallback group if it exists
        if group['fallback_group'] != []:
            for fallback_group in group['fallback_group']:
                if fallback_group in self.proxy_groups_name or fallback_group.replace(' LB', '') in self.proxy_groups_name:
                    server_include.append(fallback_group)

        # Check for keyword in server names
        for server in self.fallback_servers:
            server_name = server.get('name', '')
            if any(c in server_name for c in key_word):
                server_include.append(server_name)

        # Create Group
        self.fallback_groups.append({
            'name': group_name,
            'type': 'fallback',
            **self.health_check,
            'proxies': server_include
        })


    def create_groups(self):
        self._create_main_group()
        for group in self.config_group_details:
            if group['name'] == MAIN_GROUP:
                continue
            group_name = group['name']
            key_word = group['key_word']
            rule_type = group['type']
            fallback_enabled = group['fallback_enabled']
            server_include = []

            if fallback_enabled:
                self._create_fallback_group(group)
                group_name = group_name + ' LB'

            # Check for special tags
            for tag in SPECIAL_TAG:
                if tag in key_word:
                    server_include.append(tag)

            # Check for keyword in server names
            for server in self.main_servers:
                server_name = server.get('name', '')
                if any(c in server_name for c in key_word):
                    server_include.append(server_name)

            # Add fallback group if it exists
            if group['fallback_group'] != [] and not fallback_enabled:
                for fallback_group in group['fallback_group']:
                    if fallback_group in self.proxy_groups_name:
                        server_include.append(fallback_group)

            # Create proxy group
            if rule_type == 'url-test':
                self.proxy_groups.append({
                    'name': group_name,
                    'type': 'url-test',
                    **self.health_check,
                    'proxies': server_include
                })
            elif rule_type == 'load-balance':
                self.proxy_groups.append({
                    'name': group_name,
                    'type': 'load-balance',
                    'strategy': self.lb_strategy,
                    **self.health_check,
                    'hidden': True,
                    'proxies': server_include
                })
            elif rule_type == 'fallback':
                self.proxy_groups.append({
                    'name': group_name,
                    'type': 'fallback',
                    **self.health_check,
                    'proxies': server_include
                })
            else:
                self.proxy_groups.append({
                    'name': group_name,
                    'type': 'select',
                    'proxies': server_include
                })

    def load_main_servers(self):
        self.main_servers = self._load_servers('main_servers')
    
    def load_fallback_servers(self):
        self.fallback_servers = self._load_servers('fallback_servers')

    def create_yaml(self):
        # Create the YAML structure
        proxies = [dict(proxy) for proxy in self.main_servers + self.fallback_servers]
        self.rules.append(f'MATCH,{MAIN_GROUP}')
        proxy_groups = self.proxy_groups + self.fallback_groups
        config = {
            'proxies': proxies,
            'proxy-groups': proxy_groups,
            'rules': self.rules,
            'dns': DNS,
            'ipv6': False
        }

        # 输出为 flow-style
        yaml_str = yaml.dump(config, allow_unicode=True, sort_keys=False)

        from datetime import datetime
        file_name = f"output_Int{str(self.interval)}_{self.lb_strategy}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
        path = os.path.join(os.getcwd(), 'output', file_name)
        if not os.path.exists('./output'):
            os.makedirs('./output')
        with open(path, "w", encoding="utf-8") as f:
            f.write(yaml_str)

    def run(self):
        self.load_main_servers()
        self.load_fallback_servers()
        self.read_rules()
        self.create_groups()
        self.create_yaml()

if __name__ == "__main__":
    processor = ConfigProcessor(interval=300, lb_strategy='sticky-sessions')
    processor.run()
    processor2 = ConfigProcessor(interval=2000, lb_strategy='consistent-hashing')
    processor2.run()
    processor3 = ConfigProcessor(interval=180, lb_strategy='consistent-hashing')
    processor3.run()