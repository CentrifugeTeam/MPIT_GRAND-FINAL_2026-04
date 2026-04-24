type LogoProps = {
  pulsing?: boolean;
  /** compact — small inline 28px orb for use inside chat rows */
  compact?: boolean;
};

export const Logo = ({ pulsing = false, compact = false }: LogoProps) => {
  const cls = [
    'orb-container',
    compact && 'orb-container--compact',
    pulsing && 'orb-container--pulsing',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={cls}>
      <div className='orb'>
        <div className='orb-inner' />
        <div className='orb-inner' />
        <div className='orb-inner' />
      </div>
    </div>
  );
};
