// import firebase from "firebase";
import React, { Suspense, lazy, useEffect } from "react";
import { HashRouter, useLocation } from "react-router-dom";
import { Switch, Route } from "react-router";
import firebase from 'firebase/compat/app';
import { getFirestore, connectFirestoreEmulator, collection, getDocs } from 'firebase/firestore';
import { firebaseConfig } from "./firebase/config";
import { getFunctions, connectFunctionsEmulator } from "firebase/functions";
import { getApp } from "firebase/app";
import { getAuth, connectAuthEmulator } from "firebase/auth";

const Dashboard = lazy(() => import("./dashboard/default.js"))
const CoursePage = lazy(() => import("./course/default.js"))
const SurveyPage  = lazy(() => import("./survey/default.js"));

const GlobalHandler = () => {
  const { pathname } = useLocation();

  return null;
};

var app = null;
if (firebase.apps.length === 0) {
  app = firebase.initializeApp(firebaseConfig);
} else {
  app = firebase.apps[0]
}

const db = getFirestore(app)

// const functions = getFunctions(getApp());
// connectFunctionsEmulator(functions, "localhost", 5001);
// connectFirestoreEmulator(db, 'localhost', 8080);
// connectAuthEmulator(getAuth(), "http://localhost:9099");

const SuspenseRoute = ({ component: Component, ...props }: any) => {

  return (
    <Suspense fallback={<></>}>
      <Component {...props} />
    </Suspense>
  );
};

export const Router = () => {
  return (
    <HashRouter>
      {/*<GlobalHandler />*/}
      <Switch>

        <Route exact path="/">
          <SuspenseRoute component={Dashboard} db={db}/>
        </Route>

        <Route path="/course">
          <SuspenseRoute component={CoursePage} db={db}/>
        </Route>

        <Route path="/survey">
            <SuspenseRoute component={SurveyPage} db={db}/>
        </Route>

        <Route path="*">
          <SuspenseRoute component={Dashboard} db={db}/>
        </Route>

      </Switch>
    </HashRouter>
  );
};
