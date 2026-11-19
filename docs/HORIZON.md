# Horizon 精选

接入 [Thysrael/Horizon](https://github.com/Thysrael/Horizon) 发布的官方中文 Atom 订阅：
`https://thysrael.github.io/Horizon/feed-zh.xml`。这是作者已生成的精选内容，不是自托管 Horizon 引擎。

- 网站独立「Horizon 精选」栏目，登录用户可见，支持导航隐藏/排序。
- 近 7 期标题、分类、评分、纯文本摘要节选（最多 500 字符）、标签、原文/日报详情/社区讨论链接；不在站内复制完整分析。
- 页面打开后才请求 `/data/server-horizon.json`，默认仅显示最新一期；用户可选择全部或其他日期。
- RSS 中的日期为作者的日报期号，可能与读者本地日期不同，不代表 HotGap 抓取时间或原文发布时间。
- 每 6 小时独立拉取一次，抓取失败保留上次快照，页面对超过 48 小时未同步的内容显示提示。
- 不调用模型、不安装完整 Horizon 依赖；不经过招聘分类、飞书同步、每日岗位播报。
- 输出采用 `server-` 前缀，现有 GitHub Actions 发布规则已排除此类服务器文件，避免刷新网站时被删。

手动运行：

```sh
cd /opt/hot-gap-aggregator
.venv/bin/python -m app.capture_horizon --output /var/www/hot-gap/data/server-horizon.json
```

日志：`/var/log/hot-gap-horizon.log`；独立调度：`/etc/cron.d/hot-gap-horizon`。

部署包包括采集模块、栏目源文件、构建后的 `index.html` 和哈希 assets、安装脚本与 cron；不覆盖网站根目录权限或其他数据。
