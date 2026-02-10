import { fireEvent, render, screen } from '@testing-library/react';
import { DataTable } from './DataTable';

it('filters rows', () => {
  render(<DataTable rows={[{ ip: '1.1.1.1', status: 'allow' }, { ip: '2.2.2.2', status: 'block' }]} />);
  fireEvent.change(screen.getByPlaceholderText('search'), { target: { value: '2.2.2.2' } });
  expect(screen.getByText('2.2.2.2')).toBeInTheDocument();
});
