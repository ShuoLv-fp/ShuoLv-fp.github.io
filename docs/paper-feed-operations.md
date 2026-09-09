# 学术速递运行手册

学术速递每天读取 Google Scholar 提醒邮件，生成中英文摘要和研究关联提示，并将公开结果更新到英文 `/paper-feed/` 与中文 `/zh/paper-feed/` 页面。页面不会公开邮箱信息、邮件正文、IMAP 标识或由哪位订阅作者触发提醒。

## 首次启用

1. 立即撤销曾在聊天中披露过的 DeepSeek 密钥。不要继续使用该密钥。
2. 在 DeepSeek 控制台生成一个新密钥；在 Foxmail/QQ 邮箱的账户安全设置中开启 IMAP，并生成专用的 IMAP 授权码。
3. 打开 GitHub 仓库的 **Settings → Secrets and variables → Actions**，创建三个 Repository secrets：
   - `FOXMAIL_USERNAME`：完整邮箱地址。
   - `FOXMAIL_IMAP_AUTH_CODE`：邮箱生成的 IMAP 授权码，不是网页登录密码。
   - `DEEPSEEK_API_KEY`：新生成的 DeepSeek 密钥。
4. 不要粘贴任何密钥或授权码到聊天、源码、工作流输入、Issue、提交记录或日志中。

## 第一次安全发布

1. 打开 **Actions → Update Scholar Paper Feed → Run workflow**。
2. 保持 `lookback_days` 为 `30`，保持 `publish` 关闭，先运行预览。
3. 运行完成后下载 `paper-feed-preview`；它只包含经过校验的公开字段，并在 3 天后自动删除。
4. 检查总数、代表性的中英文摘要、相关性等级、研究关联提示、原文链接和证据标签。确认其中没有邮箱或订阅触发来源。
5. 再次手动运行，仍选 `30` 天并打开 `publish`。成功后检查：
   - 英文：`/paper-feed/`
   - 中文：`/zh/paper-feed/`
   - 前后 7 天翻页、中英文切换和原文链接。

首次发布完成后，计划任务会在每天北京时间 09:17 自动读取最近 7 天并发布。若当天没有变化，不会产生数据提交。

## 日常检查与故障处理

- **摘要暂不可用**：单篇失败会延后重试；连续 3 次失败后先发布题录卡片，后续运行仍会继续尝试补齐摘要。
- **DeepSeek 401/403**：检查新密钥是否有效、是否完整写入 `DEEPSEEK_API_KEY`，然后重新运行手动预览。不要把响应正文或密钥复制到公开位置。
- **IMAP 登录失败**：确认已开启 IMAP、`FOXMAIL_USERNAME` 为完整地址、`FOXMAIL_IMAP_AUTH_CODE` 使用授权码而不是邮箱密码。
- **限流或临时网络失败**：稍后重新运行；工作流只记录安全的错误类别和计数。
- **更换模型**：编辑 `.github/workflows/paper-feed.yml` 顶部的 `DEEPSEEK_MODEL` 普通环境变量；不要把模型名放进 Secret。
- **轮换凭据**：先在对应服务生成新凭据，再替换 GitHub Actions Secret，验证预览后撤销旧凭据。
- **暂停自动更新**：在 GitHub Actions 中打开该工作流并选择 **Disable workflow**。恢复时重新启用即可。
- **恢复数据**：在 GitHub 中找到最后一个确认正常的 `chore: update scholar paper feed` 数据提交，通过 Revert 创建恢复提交；不要强推历史。恢复后再次运行 30 天预览。

工作流会在发布前运行全部 Python/JavaScript 测试和 Jekyll 生产构建，只提交 `assets/data/paper-feed.json` 与 `paper_feed/state/retries.json`。若与 `main` 上的新修改冲突，它会中止并保留远端内容，不会强制覆盖。
