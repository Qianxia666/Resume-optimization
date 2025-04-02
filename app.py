from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import openai
import logging
import os
import sys
import time
import requests
from dotenv import load_dotenv
from urllib.parse import urlparse
import json

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for development

# 全局配置存储
current_config = {
    "api_key": os.getenv("OPENAI_API_KEY"),
    "baseUrl": os.getenv("OPENAI_API_BASE", "https://api.openai.com"),
    "model": os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo")
}

# 初始化超时设置
API_TIMEOUT = 60  # API调用超时时间（秒）
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo")
logger.info(f"初始配置: API基础URL={current_config['baseUrl']}, 模型={DEFAULT_MODEL}, 超时={API_TIMEOUT}秒")

@app.route('/')
def index():
    logger.info("访问主页")
    return send_file('index.html')

@app.route('/save_config', methods=['POST'])
def save_config():
    try:
        data = request.get_json()
        logger.info(f"收到配置数据: {data}")
        
        # 更新全局配置
        if 'apiKey' in data and data['apiKey']:
            current_config['api_key'] = data['apiKey']
            logger.info("API密钥已更新")
        
        if 'baseUrl' in data and data['baseUrl']:
            current_config['baseUrl'] = data['baseUrl']
            logger.info(f"API基础URL已更新为: {data['baseUrl']}")
            
        if 'model' in data and data['model']:
            current_config['model'] = data['model']
            logger.info(f"模型已更新为: {data['model']}")
            
        logger.info(f"当前配置: {current_config}")
        return jsonify({"message": "配置更新成功", "config": current_config})
    except Exception as e:
        logger.error(f"保存配置时出错: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

def normalize_api_url(base_url):
    """
    尝试规范化API基础URL，确保它指向正确的API端点而不是前端页面
    """
    original_url = base_url
    logger.info(f"规范化API URL: {base_url}")
    
    # 移除尾部斜杠
    base_url = base_url.rstrip('/')
    
    # 如果URL已经以/v1结尾，则无需处理
    if base_url.endswith('/v1'):
        logger.info(f"URL已经以/v1结尾，保持不变: {base_url}")
        return base_url
    
    # 如果URL看起来像网站首页，尝试添加可能的API路径
    # 检查URL路径部分是否为空或仅为 /
    parsed_url = urlparse(base_url)
    path = parsed_url.path
    
    if path == "" or path == "/":
        # 可能是网站首页，尝试添加常见的API路径
        possible_api_paths = [
            "/v1",              # OpenAI 标准路径
            "/api/v1",          # 常见API路径格式
            "/api",             # 简单API路径
            "/openai/v1"        # 一些代理使用这种格式
        ]
        
        # 记录规范化前的URL
        logger.info(f"API URL看起来像网站首页: {base_url}")
        logger.info(f"尝试以下可能的API路径: {possible_api_paths}")
        
        # 尝试直接检测/v1/chat/completions接口是否可用
        direct_chat_endpoint = f"{base_url}/v1/chat/completions"
        logger.info(f"直接测试chat completions端点: {direct_chat_endpoint}")
        
        try:
            # 仅发送简单HEAD请求测试端点是否存在
            response = requests.head(
                direct_chat_endpoint,
                timeout=5,
                headers={"Accept": "application/json"}
            )
            
            # 如果状态码不是404，该端点可能存在
            if response.status_code != 404:
                logger.info(f"找到可能的chat completions端点: {base_url}/v1")
                return f"{base_url}/v1"
        except Exception as e:
            logger.warning(f"测试chat completions端点失败: {str(e)}")
        
        # 继续测试其他可能的API路径
        for api_path in possible_api_paths:
            test_url = f"{base_url}{api_path}"
            logger.info(f"测试API路径: {test_url}")
            
            # 首先尝试测试chat completions端点
            try:
                if api_path.endswith('/v1'):
                    # 如果路径已包含/v1，则直接添加/chat/completions
                    chat_endpoint = f"{test_url}/chat/completions"
                else:
                    # 否则添加完整路径/v1/chat/completions
                    chat_endpoint = f"{test_url}/v1/chat/completions"
                
                logger.info(f"测试聊天端点: {chat_endpoint}")
                response = requests.head(
                    chat_endpoint, 
                    timeout=5,
                    headers={"Accept": "application/json"}
                )
                
                # 如果chat/completions端点可能存在
                if response.status_code != 404:
                    logger.info(f"找到可能的API路径(chat/completions): {test_url}")
                    return test_url
            except Exception as e:
                logger.warning(f"测试chat completions端点失败: {test_url}/chat/completions, 错误: {str(e)}")
            
            # 然后尝试通用models端点
            try:
                response = requests.get(
                    f"{test_url}/models", 
                    timeout=5,
                    headers={"Accept": "application/json"}
                )
                
                # 如果返回JSON并且不是HTML，可能是有效的API端点
                if response.headers.get('content-type', '').startswith('application/json'):
                    logger.info(f"找到有效的API路径: {test_url}")
                    return test_url
                elif not response.text.strip().startswith(('<!DOCTYPE', '<html')):
                    logger.info(f"可能的API路径: {test_url}")
                    return test_url
            except Exception as e:
                logger.warning(f"测试API路径失败: {test_url}, 错误: {str(e)}")
    
    # 如果没有找到更好的路径，返回原始URL
    if original_url != base_url:
        logger.info(f"使用规范化的URL: {base_url}")
        return base_url
    
    logger.info(f"保持原始URL不变: {original_url}")
    return original_url

@app.route('/chat', methods=['POST'])
def chat():
    start_time = time.time()
    try:
        data = request.get_json()
        logger.info("收到聊天请求")
        
        question = data.get('question')
        if not question:
            logger.warning("请求中没有提供问题内容")
            return jsonify({"error": "question参数不能为空"}), 400
            
        # 使用最新保存的配置或前端传入的临时配置
        api_key = data.get('apiKey', current_config['api_key'])
        api_base = data.get('baseUrl', current_config['baseUrl'])
        model = data.get('model', current_config['model'])
        
        # 获取前端传入的系统提示词，如果没有则使用默认值
        system_prompt = data.get('systemPrompt', "假如你是一名资深简历提升官，请使用STAR+改写简历，并且最后提供完整输出，帮助更多应届大学生顺利找到他们的工作 输出限制： 1.请不要使用任何表情符号 2.请在一个自然段内完整输出 3.请不要过度夸大，请符合岗位实际 4.语言请说人话，平白直叙，拒绝任何行业黑话")
        
        logger.info(f"使用配置: API基础URL={api_base}, 模型={model}")
        logger.info(f"系统提示词: {system_prompt}")
        
        if not api_key:
            logger.error("没有提供API密钥")
            return jsonify({"error": "未设置API密钥，请在配置中设置API密钥"}), 400

        # 验证API基础URL格式
        if not api_base.startswith(('http://', 'https://')):
            return jsonify({"error": "API地址格式错误，必须以http://或https://开头"}), 400
            
        # 尝试规范化API地址，确保它指向实际的API端点而不是网站首页
        api_base = normalize_api_url(api_base)
        logger.info(f"规范化后的API基础URL={api_base}")
        
        # 创建OpenAI客户端实例
        logger.info("创建OpenAI客户端实例")
        try:
            # 记录OpenAI库版本
            try:
                import pkg_resources
                openai_version = pkg_resources.get_distribution("openai").version
                logger.info(f"OpenAI库版本: {openai_version}")
            except Exception as ve:
                logger.warning(f"无法获取OpenAI版本: {str(ve)}")
                openai_version = "未知"
                
            # 对于不同版本的库，可能需要不同的初始化方式
            try:
                # 创建OpenAI客户端 (openai >= 1.0.0)
                client = openai.OpenAI(
                    api_key=api_key,
                    base_url=api_base,
                    timeout=API_TIMEOUT  # 设置超时时间
                )
                logger.info("成功使用新版方式创建OpenAI客户端")
            except (AttributeError, TypeError) as e:
                # 对于旧版本, 可能需要不同的设置方式
                logger.warning(f"新版客户端创建失败: {str(e)}，尝试兼容模式")
                
                # 设置全局配置 (openai < 1.0.0)
                openai.api_key = api_key
                openai.api_base = api_base
                client = openai  # 在旧版中，直接使用openai模块
                logger.info("已使用兼容模式设置OpenAI客户端")
                
        except Exception as e:
            logger.error(f"创建OpenAI客户端失败: {str(e)}")
            return jsonify({"error": f"API配置错误: {str(e)}"}), 500
        
        # 简单测试API连接（可选，会增加响应时间）
        try:
            # 使用轻量级请求测试连接，而不是完整models.list()
            logger.info(f"测试API服务可用性: {api_base}")
            
            # 先尝试用HEAD请求检查服务是否在线
            try:
                head_response = requests.head(api_base, timeout=5)
                if head_response.status_code >= 400:
                    logger.warning(f"API服务HEAD请求返回错误状态: {head_response.status_code}")
                else:
                    logger.info(f"API服务响应正常: {head_response.status_code}")
            except Exception as head_error:
                logger.warning(f"API服务HEAD请求失败: {str(head_error)}")
            
            # 然后尝试models接口
            test_url = f"{api_base}/v1/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            
            # 增加超时，避免长时间等待
            test_response = requests.get(test_url, headers=headers, timeout=10)
            
            if test_response.status_code == 404:
                # 尝试其他可能的路径
                alt_test_url = f"{api_base}/models"
                logger.info(f"标准models路径不存在，尝试备用路径: {alt_test_url}")
                test_response = requests.get(alt_test_url, headers=headers, timeout=5)
            
            # 即使状态码不是200，我们也不立即失败，只记录警告
            if test_response.status_code != 200:
                warning_msg = f"API连接测试返回非200状态码: {test_response.status_code}"
                logger.warning(warning_msg)
                # 只在明确是认证问题时才直接返回错误
                if test_response.status_code == 401:
                    error_msg = f"API密钥认证失败: {test_response.status_code}"
                    logger.error(error_msg)
                    return jsonify({"error": error_msg}), 500
            else:
                logger.info("API连接测试成功")
                
        except requests.exceptions.RequestException as e:
            warning_msg = f"API连接测试失败: {str(e)}"
            logger.warning(warning_msg)
            # 这里我们只记录警告，但仍尝试进行实际请求
            # 因为有些API代理可能不支持models端点，但仍能处理聊天请求
        
        # 开始调用API
        logger.info("开始调用OpenAI API")
        
        try:
            # 设置最大重试次数
            max_retries = 2
            retries = 0
            last_error = None
            
            while retries <= max_retries:
                try:
                    # 使用OpenAI 1.x版本的API调用方式
                    try:
                        # 首先尝试使用新版API调用方式 (openai >= 1.0.0)
                        logger.info("使用OpenAI 1.x版本的API调用")
                        
                        # 确保请求参数格式正确
                        messages = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": question}
                        ]
                        
                        # 设置请求参数
                        request_params = {
                            "model": model,
                            "messages": messages
                        }
                        
                        # 记录请求内容，便于调试
                        logger.info(f"OpenAI请求参数: {request_params}")
                        
                        # 调用API
                        response = client.chat.completions.create(**request_params)
                        logger.info(f"新版API调用成功，耗时: {time.time() - start_time:.2f}秒")
                        
                        # 检查响应类型
                        logger.info(f"响应类型: {type(response)}")
                        
                        # 正确提取答案
                        answer = extract_answer_from_response(response, logger)
                        
                    except (AttributeError, ImportError, ValueError) as e:
                        logger.warning(f"新版API调用失败，尝试使用兼容模式: {str(e)}")
                        
                        try:
                            # 使用直接HTTP请求方式作为备选方案
                            headers = {
                                "Content-Type": "application/json",
                                "Authorization": f"Bearer {api_key}"
                            }
                            
                            payload = {
                                "model": model,
                                "messages": [
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": question}
                                ]
                            }
                            
                            # 首先尝试测试/v1/chat/completions端点
                            if api_base.rstrip('/').endswith('/v1'):
                                # 如果基础URL已经以/v1结尾，直接添加/chat/completions
                                chat_completions_url = f"{api_base.rstrip('/')}/chat/completions"
                                logger.info(f"优先测试chat completions端点(基础URL已包含/v1): {chat_completions_url}")
                            else:
                                # 否则添加完整路径/v1/chat/completions
                                chat_completions_url = f"{api_base.rstrip('/')}/v1/chat/completions"
                                logger.info(f"优先测试chat completions端点: {chat_completions_url}")
                            
                            logger.info(f"使用HTTP请求调用API: {chat_completions_url}")
                            logger.info(f"请求参数: {payload}")
                            
                            # 发送HTTP请求
                            response = requests.post(
                                chat_completions_url,
                                headers=headers,
                                json=payload,
                                timeout=API_TIMEOUT
                            )
                            
                            # 检查HTTP响应状态
                            if response.status_code != 200:
                                error_msg = f"API返回错误状态码: {response.status_code}, 响应: {response.text}"
                                logger.error(error_msg)
                                raise Exception(error_msg)
                            
                            # 解析JSON响应
                            response_data = response.json()
                            logger.info("HTTP请求API调用成功")
                            
                            # 检查响应格式并提取答案
                            answer = extract_answer_from_response(response_data, logger)
                        
                        except Exception as http_error:
                            logger.error(f"HTTP请求模式失败: {str(http_error)}")
                            # 如果前两种方式都失败，再尝试completions接口
                            completions_url = f"{api_base.rstrip('/')}/v1/completions"
                            
                            simple_payload = {
                                "model": model,
                                "prompt": f"系统: {system_prompt}\n\n用户: {question}",
                                "max_tokens": 2000,
                                "temperature": 0.7
                            }
                            
                            logger.info(f"尝试completions接口: {completions_url}")
                            logger.info(f"请求参数: {simple_payload}")
                            
                            completions_response = requests.post(
                                completions_url,
                                headers=headers,
                                json=simple_payload,
                                timeout=API_TIMEOUT
                            )
                            
                            if completions_response.status_code != 200:
                                error_msg = f"Completions接口返回错误: {completions_response.status_code}, 响应: {completions_response.text}"
                                logger.error(error_msg)
                                raise Exception(error_msg)
                            
                            completions_data = completions_response.json()
                            logger.info("Completions接口调用成功")
                            
                            answer = extract_answer_from_response(completions_data, logger)
                    
                    logger.info(f"成功获取API响应，总耗时: {time.time() - start_time:.2f}秒")
                    return jsonify({"answer": answer})
                    
                except Exception as e:
                    last_error = e
                    retries += 1
                    logger.warning(f"API调用失败，重试 {retries}/{max_retries}: {str(e)}")
                    if retries <= max_retries:
                        time.sleep(2)  # 短暂延迟后重试
            
            # 如果所有重试都失败
            logger.error(f"所有API调用重试都失败: {str(last_error)}")
            return jsonify({"error": f"OpenAI API调用失败: {str(last_error)}"}), 500
            
        except Exception as e:
            logger.error(f"调用OpenAI API时出错: {str(e)}")
            return jsonify({"error": f"调用OpenAI API时出错: {str(e)}"}), 500

    except Exception as e:
        logger.error(f"处理聊天请求时出错: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        logger.info(f"请求处理总耗时: {time.time() - start_time:.2f}秒")

@app.route('/get_config', methods=['GET'])
def get_config():
    try:
        # 返回当前配置，但不包含API密钥的完整值
        safe_config = {
            "baseUrl": current_config['baseUrl'],
            "model": current_config['model'],
            # 如果有API密钥，只返回前6位和后4位，中间用***替代
            "apiKey": mask_api_key(current_config['api_key']) if current_config['api_key'] else ""
        }
        logger.info("请求当前配置")
        return jsonify({"config": safe_config})
    except Exception as e:
        logger.error(f"获取配置时出错: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

def mask_api_key(api_key):
    """遮盖API密钥，只显示前6位和后4位"""
    if not api_key or len(api_key) < 10:
        return ""
    return api_key[:6] + "***" + api_key[-4:]

@app.route('/test_api', methods=['POST'])
def test_api():
    """测试API连接并检测正确的API路径"""
    try:
        data = request.get_json()
        logger.info("收到API测试请求")
        
        api_key = data.get('apiKey')
        base_url = data.get('baseUrl', 'https://api.openai.com')
        
        if not api_key:
            return jsonify({"success": False, "error": "未提供API密钥"}), 400
            
        if not base_url.startswith(('http://', 'https://')):
            return jsonify({"success": False, "error": "API地址格式错误，必须以http://或https://开头"}), 400
        
        logger.info(f"测试API连接: {base_url}")
        
        # 尝试检测正确的API路径
        detected_url = None
        html_response = False
        
        # 先尝试直接测试提供的URL
        try:
            # 发送简单的API请求
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # 首先尝试测试/v1/chat/completions端点
            if base_url.rstrip('/').endswith('/v1'):
                # 如果基础URL已经以/v1结尾，直接添加/chat/completions
                chat_completions_url = f"{base_url.rstrip('/')}/chat/completions"
                logger.info(f"优先测试chat completions端点(基础URL已包含/v1): {chat_completions_url}")
            else:
                # 否则添加完整路径/v1/chat/completions
                chat_completions_url = f"{base_url.rstrip('/')}/v1/chat/completions"
                logger.info(f"优先测试chat completions端点: {chat_completions_url}")
            
            try:
                # 轻量级OPTIONS请求测试端点是否存在
                options_response = requests.options(chat_completions_url, timeout=5, headers=headers)
                # 如果接口可能存在
                if options_response.status_code != 404:
                    logger.info(f"chat completions端点可能存在")
                    # 推测正确的基础URL
                    detected_url = f"{base_url.rstrip('/')}/v1"
                    if detected_url.endswith('/v1/v1'):  # 避免重复v1
                        detected_url = detected_url[:-3]
                    return jsonify({
                        "success": True, 
                        "message": "找到可能的API端点: /v1/chat/completions", 
                        "detectedUrl": detected_url
                    })
            except Exception as e:
                logger.warning(f"测试chat completions端点失败: {str(e)}")
            
            # 如果直接测试chat completions失败，尝试标准模型列表请求
            test_url = f"{base_url.rstrip('/')}/v1/models"
            logger.info(f"测试API端点: {test_url}")
            
            response = requests.get(test_url, headers=headers, timeout=10)
            
            # 检查响应类型
            content_type = response.headers.get('content-type', '')
            logger.info(f"API响应类型: {content_type}")
            
            # 如果响应是HTML而不是JSON，可能是前端页面
            if 'text/html' in content_type.lower() or response.text.strip().startswith(('<!DOCTYPE', '<html')):
                html_response = True
                logger.warning("API返回了HTML内容，可能不是正确的API端点")
                # 获取页面标题作为额外信息
                try:
                    import re
                    title_match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE)
                    if title_match:
                        title = title_match.group(1)
                        logger.info(f"HTML页面标题: {title}")
                except:
                    pass
            elif response.status_code == 200 and 'application/json' in content_type.lower():
                # 成功获取JSON响应
                logger.info("成功连接到API端点")
                detected_url = base_url
            
        except Exception as e:
            logger.warning(f"直接测试URL失败: {str(e)}")
        
        # 如果直接测试失败或返回HTML，尝试规范化URL
        if html_response or detected_url is None:
            normalized_url = normalize_api_url(base_url)
            if normalized_url != base_url:
                logger.info(f"尝试规范化的URL: {normalized_url}")
                
                try:
                    # 尝试使用规范化的URL
                    test_url = f"{normalized_url.rstrip('/')}/models"
                    response = requests.get(test_url, headers=headers, timeout=10)
                    
                    if response.status_code == 200 and 'application/json' in response.headers.get('content-type', '').lower():
                        logger.info(f"规范化URL连接成功: {normalized_url}")
                        detected_url = normalized_url
                    else:
                        # 尝试另一个常见路径
                        test_url = f"{normalized_url.rstrip('/')}/v1/models"
                        response = requests.get(test_url, headers=headers, timeout=10)
                        if response.status_code == 200 and 'application/json' in response.headers.get('content-type', '').lower():
                            logger.info(f"规范化URL(v1)连接成功: {normalized_url}")
                            detected_url = normalized_url
                            
                except Exception as e:
                    logger.warning(f"测试规范化URL失败: {str(e)}")
                    
        # 返回测试结果
        if detected_url:
            return jsonify({
                "success": True, 
                "message": "API连接成功", 
                "detectedUrl": detected_url
            })
        elif html_response:
            return jsonify({
                "success": False, 
                "error": "API地址返回了HTML页面，而不是API端点。请检查地址格式，通常需要添加/api/v1或/v1等路径。"
            })
        else:
            return jsonify({
                "success": False, 
                "error": "无法连接到API。请检查API地址和密钥是否正确。"
            })
            
    except Exception as e:
        logger.error(f"API测试失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": f"测试过程出错: {str(e)}"})

def extract_answer_from_response(response_obj, logger):
    """
    从OpenAI API响应中提取答案，适应不同的响应格式
    """
    try:
        # 检查是否为Python对象(OpenAI SDK的响应对象)
        if hasattr(response_obj, 'choices'):
            logger.info("检测到OpenAI SDK响应对象")
            # 尝试通过属性访问
            if len(response_obj.choices) > 0:
                choice = response_obj.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    return choice.message.content
                elif hasattr(choice, 'text'):
                    return choice.text
        
        # 检查是否可以转换为字典(Pydantic对象)
        if hasattr(response_obj, 'model_dump'):
            logger.info("尝试将Pydantic对象转换为字典")
            response_dict = response_obj.model_dump()
        elif hasattr(response_obj, 'dict'):
            logger.info("尝试使用.dict()方法")
            response_dict = response_obj.dict()
        else:
            # 假设已经是字典或可以直接索引
            response_dict = response_obj
        
        # 如果是字典，尝试通过键访问
        if isinstance(response_dict, dict):
            logger.info("使用字典访问方式解析")
            if "choices" in response_dict and len(response_dict["choices"]) > 0:
                choice = response_dict["choices"][0]
                if isinstance(choice, dict):
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"]
                    elif "text" in choice:
                        return choice["text"]
                    elif "content" in choice:
                        return choice["content"]
        
        # 如果是JSON响应字符串，尝试解析
        if isinstance(response_obj, str):
            logger.info("尝试解析JSON字符串")
            import json
            try:
                json_data = json.loads(response_obj)
                if "choices" in json_data and len(json_data["choices"]) > 0:
                    choice = json_data["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"]
                    elif "text" in choice:
                        return choice["text"]
            except json.JSONDecodeError:
                # 不是有效的JSON
                pass
        
        # 如果上面的方法都失败，记录详细信息并返回字符串表示
        logger.warning(f"无法用标准方式提取答案，响应类型: {type(response_obj)}")
        logger.warning(f"响应内容: {str(response_obj)[:200]}...")
        
        # 最后的尝试：直接返回字符串表示
        if hasattr(response_obj, 'content'):
            return response_obj.content
        elif hasattr(response_obj, 'text'):
            return response_obj.text
        
        return str(response_obj)
    
    except Exception as e:
        logger.error(f"提取答案时出错: {str(e)}")
        return f"无法解析API响应: {str(e)}"

if __name__ == '__main__':
    # 初始化日志设置
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 获取当前配置
    API_BASE = current_config['baseUrl']
    MODEL = current_config['model']
    TIMEOUT = API_TIMEOUT
    
    # 打印初始配置信息
    logger.info(f"初始配置: API基础URL={API_BASE}, 模型={MODEL}, 超时={TIMEOUT}秒")
    
    # 明确指定主机为0.0.0.0确保可从任何IP访问，使用端口8080并关闭调试模式
    logger.info(f"启动Flask应用，监听所有接口，端口8080")
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
