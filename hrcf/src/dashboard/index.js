import React, { useEffect, useState } from 'react';
import StyledFirebaseAuth from 'react-firebaseui/StyledFirebaseAuth';
import firebase from 'firebase/compat/app';
import 'firebase/compat/auth';
import "bootstrap/dist/css/bootstrap.min.css";
import "../feedback/feedback.css"
import { getFirestore, connectFirestoreEmulator, collection, getDocs } from 'firebase/firestore';
import { firebaseConfig } from "../firebase/config";
import { CoursesTable } from "./coursesTable.js"
import { AddCourse } from "./addCourse.js"
import { Loading } from "./loading/Loading.js"

import { getApp } from "firebase/app";
import { getFunctions, connectFunctionsEmulator } from "firebase/functions";

import { getAuth, connectAuthEmulator } from "firebase/auth";

export const Dashboard = (prop) => {
  const db = prop.db
  const [signedIn, setSignedIn] = useState(false);
  const coursesState = useState([])
  const courseIdState = useState([])

  const uiConfig = {
    signInOptions: [
      {
        provider: firebase.auth.GoogleAuthProvider.PROVIDER_ID,
        customParameters: {
          hd: 'stanford.edu',
          auth_type: 'reauthenticate',
          prompt: 'select_account'
        },
        providerName:'Stanford',
        buttonColor:'red',
        iconUrl:'https://identity.stanford.edu/wp-content/uploads/2020/07/SU_SealColor_web3-1.png'
      },
      // firebase.auth.GoogleAuthProvider.PROVIDER_ID,
      // firebase.auth.EmailAuthProvider.PROVIDER_ID
    ],
    signInFlow: 'redirect',
    immediateFederatedRedirect:true
    // Other config options...
  };

  useEffect(() => {
    const unregisterAuthObserver = firebase.auth()
      .onAuthStateChanged(user => {
        setSignedIn(!!user);
      })
    return () => unregisterAuthObserver(); // Make sure we un-register Firebase observers when the component unmounts.
  }, []);


  if (signedIn){
    return (
      <>
      <div className="container">
      <div className="row">
      <div className="col">
        <div className="card mt-4 mx-auto" style={{maxWidth: 800}}>
          <div className="card-body">
            <h1>High-Resolution Course Evaluation</h1>
            <hr/>
            <h4>Welcome {firebase.auth().currentUser.displayName}</h4>
            <a href="" onClick={() => firebase.auth().signOut()}>
              Sign-out
            </a>
          </div>
        </div>
        <CoursesTable db={db} coursesState={coursesState}
          courseIdState={courseIdState}
          user={firebase.auth().currentUser}/>
        <AddCourse db={db} coursesState={coursesState}
          courseIdState={courseIdState}
          user={firebase.auth().currentUser}/>
      </div>
      </div>
      </div>
      </>
    )
  } else {
    return (
      <>
        <StyledFirebaseAuth uiConfig={uiConfig} firebaseAuth={firebase.auth()} />
      </>
    )
  }
}
