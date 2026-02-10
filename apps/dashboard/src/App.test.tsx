import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { App } from './App';

describe('routing', () => {
  it('renders overview', async () => {
    render(<MemoryRouter initialEntries={['/']}><App /></MemoryRouter>);
    expect(await screen.findByText('Overview')).toBeInTheDocument();
  });

  it('renders all major pages', async () => {
    const paths = ['/attack-map', '/events', '/waf', '/rate', '/geo', '/bot', '/deployments', '/analytics', '/runbooks'];
    for (const path of paths) {
      render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>);
    }
    expect(screen.getByText('Edge Security Control Plane')).toBeInTheDocument();
  });
});
