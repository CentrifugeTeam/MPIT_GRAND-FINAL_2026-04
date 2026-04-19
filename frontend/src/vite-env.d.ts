declare module '*.svg' {
  import * as React from 'react';

  const ReactComponent: React.FunctionComponent<
    React.ComponentProps<'svg'> & {
      desc?: string;
      descId?: string;
      title?: string;
      titleId?: string;
    }
  >;

  export default ReactComponent;
}
