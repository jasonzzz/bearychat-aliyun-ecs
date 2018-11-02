## 作品名称

阿里云服务器控制

## 创意描述

通过 bearychat 直接对阿里云服务器进行一些操作
可以直接在聊天里面查看机器状态，或是根据聊天结论动态调整机器
达到聊天内分享以及避免繁琐的网页操作的目的

aliyun 实际网页操作参数非常多，`create` 定位主要在日常频繁需要创建的实例类型
bearychat outgoing 回复有字数限制，部分会返回大量文本的命令譬如 `avail-*` 还是不太好用

之前考虑过用滴滴云，不过 api 不提供或是需要企业用户，只好改用 aliyun 了

## 使用

### help

帮助页面

![help](https://github.com/jasonzzz/bearychat-aliyun-ecs/blob/master/pics/help.png)

### list

显示某区域的实例

![list](https://github.com/jasonzzz/bearychat-aliyun-ecs/blob/master/pics/list.png)

### show

显示某区域实例的详细状态

![show](https://github.com/jasonzzz/bearychat-aliyun-ecs/blob/master/pics/show.png)

### start

开启某区域实例

![start](https://github.com/jasonzzz/bearychat-aliyun-ecs/blob/master/pics/start.png)

### stop

停止某区域实例

![stop](https://github.com/jasonzzz/bearychat-aliyun-ecs/blob/master/pics/stop.png)

### create

创建某区域一个实例

需要手动在网页端建立好 LaunchTemplate
绑定 eip 需要 ecs 处于 running 状态，考虑到应用启动，默认等待 30s
没有返回，可以执行 `create` 后再执行 `show/list` 查看状态

![create](https://github.com/jasonzzz/bearychat-aliyun-ecs/blob/master/pics/create.png)

### delete

删除某区域一个实例

![delete1](https://github.com/jasonzzz/bearychat-aliyun-ecs/blob/master/pics/delete1.png)

![delete2](https://github.com/jasonzzz/bearychat-aliyun-ecs/blob/master/pics/delete2.png)

![delete3](https://github.com/jasonzzz/bearychat-aliyun-ecs/blob/master/pics/delete3.png)

![delete4](https://github.com/jasonzzz/bearychat-aliyun-ecs/blob/master/pics/delete4.png)

![delete5](https://github.com/jasonzzz/bearychat-aliyun-ecs/blob/master/pics/delete5.png)

### monitor-5min

显示某区域某个实例最近 5min 监控信息

数据实在太多，只选择了最近 5min 数据，供参考

![monitor](https://github.com/jasonzzz/bearychat-aliyun-ecs/blob/master/pics/monitor.png)

### avail-regions

显示可用区域，常用区域一般可以记住，用来查不常用区域

![avail-regions](https://github.com/jasonzzz/bearychat-aliyun-ecs/blob/master/pics/avail-regions.png)

### avail-zones

显示可用地域，因为是用 launch template 创建实例，没什么用

![avail-zones](https://github.com/jasonzzz/bearychat-aliyun-ecs/blob/master/pics/avail-zones.png)

### avail-images

显示可用镜像，因为是用 launch template 创建实例，所以没什么用

![avail-images](https://github.com/jasonzzz/bearychat-aliyun-ecs/blob/master/pics/avail-images.png)

## 部署

因为 aliyun token 不能公开，不能公开测试

1. `$ sudo pip3 install -r requirements.txt`

2. 填一下 handlers/base.py token 和 handlers/aliyun.py aliyun_token

3. `python3 ./webhook.py --modules='aliyun'`

4. bearychat 配置 outgoing
