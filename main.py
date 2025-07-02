from logging import config
import os
import yaml

MAIN_RULES = '🚀 节点选择'

SPECIAL_TAG = ['REJECT', 'DIRECT', 'MAIN']

URL_TEST_CONFIG = {
    'type': 'url-test',
    'url': 'http://www.qq.com/',
    'interval': 7200,
    'tolerance': 1,
    'timeout': 1000,
    'max-failed-times': 1
}

DNS = {
    'enable': True,
    'ipv6': False,
    'default-nameserver': ['223.5.5.5', '119.29.29.29'],
    'enhanced-mode': 'fake-ip',
    'fake-ip-range': '198.18.0.1/16',
    'use-hosts': True,
    'nameserver': ['https://doh.pub/dns-query', 'https://dns.alidns.com/dns-query'],
    'fallback': ['https://doh.dns.sb/dns-query', 'https://dns.cloudflare.com/dns-query', 'https://dns.twnic.tw/dns-query', 'tls://8.8.4.4:853'],
    'fallback-filter': { 'geoip': True, 'ipcidr': ['240.0.0.0/4', '0.0.0.0/32'] }
}

class FlowStyleList(list):
    pass

def represent_flow_style_list(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)

yaml.add_representer(FlowStyleList, represent_flow_style_list)

class ConfigProcessor:
    def __init__(self):
        self.rules = []
        self.proxy_groups_name = []
        self.config_group_details = []
        self.proxy_groups = []
        self.main_servers = []
        self.fallback_servers = []
        pass

    def _list_folder_files(self, folder_path):
        """
        List all files in the specified folder.
        :param folder_path: Path to the folder.
        :return: List of file names in the folder.
        """
        return [
            f for f in os.listdir(f'./{folder_path}')
            if os.path.isfile(os.path.join(f'./{folder_path}', f)) and f.endswith('.yaml')
        ]

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
            key_word = data['key_word']
            rules = data['rules']
            rule_type = data.get('type', 'select')
            self._rules_process(group_name, rules)
            self.proxy_groups_name.append(group_name)

            self.config_group_details.append({
                'name': group_name,
                'key_word': key_word,
                'type': rule_type
            })

    def _create_main_group(self):
        proxies = self.proxy_groups_name
        proxies.extend(['DIRECT', 'REJECT'])
        main_server_names = [server.get('name', '') for server in self.main_servers]
        proxies.extend(main_server_names)
        fallback_server_names = [server.get('name', '') for server in self.fallback_servers]
        proxies.extend(fallback_server_names)

        self.proxy_groups.append({
            'name': MAIN_RULES,
            'type': 'select',
            'proxies': proxies
        })

    def _create_fallback_group(self):
        fallback_servers = [server.get('name', '') for server in self.fallback_servers]
        if fallback_servers:
            self.proxy_groups.append({
                'name': '🛟备用节点',
                'type': 'fallback',
                'proxies': fallback_servers
            })
    def create_groups(self):
        self._create_main_group()
        for group in self.config_group_details:
            group_name = group['name']
            key_word = group['key_word']
            rule_type = group['type']
            server_include = []

            # Check for special tags
            for tag in SPECIAL_TAG:
                if tag in key_word:
                    if tag == 'MAIN':
                        server_include.append(MAIN_RULES)
                    else:
                        server_include.append(tag)

            # Check for keyword in server names
            for server in self.main_servers:
                server_name = server.get('name', '')
                if any(c in server_name for c in key_word):
                    server_include.append(server_name)

            # Create proxy group
            if rule_type == 'url-test':
                self.proxy_groups.append({
                    'name': group_name,
                    **URL_TEST_CONFIG,
                    'proxies': server_include
                })
            else:
                self.proxy_groups.append({
                    'name': group_name,
                    'type': 'select',
                    'proxies': server_include
                })
        self._create_fallback_group()

    def load_main_servers(self):
        self.main_servers = self._load_servers('main_servers')
    
    def load_fallback_servers(self):
        self.fallback_servers = self._load_servers('fallback_servers')

    def create_yaml(self):
        # Create the YAML structure
        proxies = [dict(proxy) for proxy in self.main_servers + self.fallback_servers]
        self.rules.append(f'MATCH,{MAIN_RULES}')

        config = {
            'proxies': proxies,
            'proxy-groups': self.proxy_groups,
            'rules': self.rules,
            'dns': DNS
        }

        # 输出为 flow-style
        yaml_str = yaml.dump(config, allow_unicode=True, sort_keys=False)

        from datetime import datetime
        file_name = f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
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
    processor = ConfigProcessor()
    processor.run()