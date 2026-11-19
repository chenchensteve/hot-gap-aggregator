import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, it } from 'vitest';
import HorizonView, { type HorizonFeed } from './HorizonView';

afterEach(cleanup);

const feed: HorizonFeed = {
  generated_at: new Date().toISOString(), latest_issue: '2026-11-18',
  issues: [{ date: '2026-11-18', url: 'https://example.org/daily', item_count: 2 }],
  items: [
    { id: '1', title: '推理优化', url: 'https://example.org/1', digest_url: 'https://example.org/daily#1', issue_date: '2026-11-18', category: '科技新闻', score: 9, summary: '推理速度提升', tags: ['AI'], discussion_url: '' },
    { id: '2', title: '工程实践', url: 'https://example.org/2', digest_url: 'https://example.org/daily#2', issue_date: '2026-11-18', category: '科技博客', score: 7, summary: '工程经验', tags: [], discussion_url: '' },
  ],
};

it('filters actual stories and links both original and attributed digest', () => {
  render(<HorizonView feed={feed} />);
  expect(screen.getByRole('link', { name: '推理优化' })).toHaveAttribute('href', 'https://example.org/1');
  expect(screen.getAllByRole('link', { name: '日报详情 ↗' })[0]).toHaveAttribute('href', 'https://example.org/daily#1');
  fireEvent.change(screen.getByLabelText('Horizon 最低评分'), { target: { value: '8' } });
  expect(screen.queryByText('工程实践')).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('搜索 Horizon'), { target: { value: '不存在' } });
  expect(screen.getByText('没有符合当前筛选条件的资讯。')).toBeInTheDocument();
});

it('renders external text without interpreting markup', () => {
  render(<HorizonView feed={{ ...feed, items: [{ ...feed.items[0], summary: '<img src=x onerror=alert(1)>' }] }} />);
  expect(screen.getByText('<img src=x onerror=alert(1)>')).toBeInTheDocument();
  expect(document.querySelector('img')).toBeNull();
});
