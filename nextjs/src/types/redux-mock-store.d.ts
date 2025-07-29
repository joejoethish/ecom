declare module 'redux-mock-store' {
  import { Middleware, Store, AnyAction } from 'redux';
  
  export interface MockStoreCreator<S = any, A extends AnyAction = AnyAction> {
    (state?: S): MockStore<S, A>;
  }
  
  export interface MockStore<S = any, A extends AnyAction = AnyAction> extends Store<S, A> {
    getActions(): A[];
    clearActions(): void;
  }
  
  export default function configureStore<S = any, A extends AnyAction = AnyAction>(
    middlewares?: Middleware[]
  ): MockStoreCreator<S, A>;
}