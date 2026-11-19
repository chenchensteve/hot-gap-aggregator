import { useState } from 'react';

type HorizonItem = {
  id: string; title: string; url: string; digest_url: string; issue_date: string;
  category: string; score: number | null; summary: string; tags: string[]; discussion_url: string;
};
export type HorizonFeed = {
  generated_at: string; latest_issue: string;
  issues: { date: string; url: string; item_count: number }[];
  items: HorizonItem[];
};

export default function HorizonView({ feed, error }: { feed: HorizonFeed | null; error?: string }) {
  const [issue, setIssue] = useState('latest');
  const [category, setCategory] = useState('all');
  const [minimum, setMinimum] = useState(0);
  const [query, setQuery] = useState('');
  const date = issue === 'latest' ? feed?.latest_issue : issue;
  const categories = [...new Set((feed?.items ?? []).map((item) => item.category))];
  const items = (feed?.items ?? []).filter((item) =>
    (issue === 'all' || item.issue_date === date)
    && (category === 'all' || item.category === category)
    && (minimum === 0 || (item.score ?? -1) >= minimum)
    && `${item.title} ${item.summary} ${item.tags.join(' ')}`.toLocaleLowerCase().includes(query.toLocaleLowerCase().trim()),
  );
  const stale = feed?.generated_at && Date.now() - Date.parse(feed.generated_at) > 48 * 3600 * 1000;
  return <section aria-label="Horizon 精选资讯" className="space-y-5">
    <header className="rounded-2xl border border-[var(--line)] bg-[var(--soft)] p-5">
      <h2 className="text-xl font-black">Horizon 精选</h2>
      <p className="mt-2 text-sm text-[var(--muted)]">Horizon · Thysrael 筛选的中文日报，涵盖科技新闻、技术文章与其他主题。评分来自 Horizon；点击原文可核对信息。</p>
      <a href="https://thysrael.github.io/Horizon/" target="_blank" rel="noopener noreferrer" className="mt-3 inline-block text-sm font-bold text-sky-600">Horizon 日报官网 ↗</a>
      {feed && <p className="mt-2 text-xs text-[var(--muted)]">最新一期 {feed.latest_issue} · 已同步 {feed.issues.length} 期 · 上次同步 {new Date(feed.generated_at).toLocaleString()}</p>}
    </header>
    {(error || stale) && <p role="alert" className="rounded-xl bg-amber-100 p-3 text-sm text-amber-900">{error ? '本次加载失败，请稍后刷新。' : '同步已超过 48 小时，以下为上次成功的内容。'}</p>}
    {feed && <>
      <div className="flex flex-wrap gap-3 text-sm">
        <select aria-label="Horizon 日报日期" value={issue} onChange={(e) => setIssue(e.target.value)} className="max-w-full rounded-xl border border-[var(--line)] bg-[var(--paper)] p-2">
          <option value="latest">最新一期</option><option value="all">最近全部</option>
          {feed.issues.map((entry) => <option key={entry.date} value={entry.date}>{entry.date}（{entry.item_count}条）</option>)}
        </select>
        <select aria-label="Horizon 分类" value={category} onChange={(e) => setCategory(e.target.value)} className="rounded-xl border border-[var(--line)] bg-[var(--paper)] p-2">
          <option value="all">全部分类</option>{categories.map((value) => <option key={value}>{value}</option>)}
        </select>
        <select aria-label="Horizon 最低评分" value={minimum} onChange={(e) => setMinimum(Number(e.target.value))} className="rounded-xl border border-[var(--line)] bg-[var(--paper)] p-2">
          <option value={0}>全部评分</option><option value={7}>7分及以上</option><option value={8}>8分及以上</option><option value={9}>9分及以上</option>
        </select>
        <input aria-label="搜索 Horizon" placeholder="搜索标题、摘要或标签" value={query} onChange={(e) => setQuery(e.target.value)} className="min-w-0 flex-1 rounded-xl border border-[var(--line)] bg-[var(--paper)] p-2" />
      </div>
      <p className="text-xs text-[var(--muted)]">{items.length} 条 · 摘要节选，完整背景与分析见日报详情</p>
      <div className="grid gap-4 md:grid-cols-2">{items.map((item) => <article key={item.id} className="min-w-0 rounded-2xl border border-[var(--line)] p-5">
        <div className="mb-3 flex flex-wrap gap-2 text-xs text-[var(--muted)]"><span>{item.issue_date}</span><span>{item.category}</span>{item.score !== null && <span className="font-bold text-amber-600">Horizon {item.score.toFixed(1)}/10</span>}</div>
        <h3 className="break-words text-lg font-bold"><a href={item.url} target="_blank" rel="noopener noreferrer" className="hover:text-sky-600">{item.title}</a></h3>
        <p className="mt-3 break-words text-sm leading-7 text-[var(--muted)]">{item.summary || '打开日报查看详细内容。'}</p>
        <div className="mt-3 flex flex-wrap gap-2">{item.tags.map((tag) => <span key={tag} className="max-w-full break-words rounded-full bg-[var(--soft)] px-2 py-1 text-xs">{tag}</span>)}</div>
        <div className="mt-4 flex flex-wrap gap-4 text-sm font-bold text-sky-600">
          <a href={item.url} target="_blank" rel="noopener noreferrer">阅读原文 ↗</a>
          <a href={item.digest_url} target="_blank" rel="noopener noreferrer">日报详情 ↗</a>
          {item.discussion_url && <a href={item.discussion_url} target="_blank" rel="noopener noreferrer">社区讨论 ↗</a>}
        </div>
      </article>)}</div>
      {items.length === 0 && <p className="py-10 text-center text-[var(--muted)]">没有符合当前筛选条件的资讯。</p>}
    </>}
    {!feed && !error && <p className="py-10 text-center text-[var(--muted)]">Horizon 暂无已同步数据。</p>}
  </section>;
}
