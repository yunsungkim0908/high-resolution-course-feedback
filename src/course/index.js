import { Button, ButtonGroup, Dropdown, Table } from "react-bootstrap";
import React, { useState, useEffect } from 'react';
// import firebase from "firebase";
import firebase from 'firebase/compat/app';
import 'firebase/compat/auth';
import "bootstrap/dist/css/bootstrap.min.css";
import "../feedback/feedback.css"
import { CSVReader } from 'react-papaparse';
import { Link, useLocation } from 'react-router-dom'
import Swal from "sweetalert2"
import { initializeApp } from 'firebase/app';
import { firebaseConfig } from "../firebase/config";
import { getFirestore, collection, getDocs } from 'firebase/firestore';
import { doc, deleteDoc, setDoc, getDoc } from "firebase/firestore";
import { AddQuestions } from './addQuestions.js'
import { ManageAdmins } from "./admins.js"
import { getAuth, onAuthStateChanged } from "firebase/auth";


// TODO: explain timeline

function useQuery() {
  return new URLSearchParams(useLocation().search);
}

const SuccessMessage = (succMsg) => {
    Swal.fire({
      icon: "success",
      title: succMsg
    })
}
const ErrorMessage = (errorMsg) => {
    Swal.fire({
      icon: "error",
      title: errorMsg,
    })
}

export const CoursePage = (prop) => {
  const [signedIn, setSignedIn] = useState(false)
  const [userEmail, setUserEmail] = useState(null)

  let queryParams = useQuery();
  let className = queryParams.get('callNumber')
  let instructorHash = queryParams.get('classHash')
  
  const db = prop.db

  useEffect(() => {
    const unregisterAuthObserver = firebase.auth()
      .onAuthStateChanged(user => {
        setSignedIn(!!user);
        setUserEmail(user.email)
      })
    return () => unregisterAuthObserver(); // Make sure we un-register Firebase observers when the component unmounts.
  }, []);

  return (
    <>
      <div className="container">
        <div className="row">
          <div className="col">
            <div className="card mt-4 mx-auto" style={{maxWidth: 800}}>
              <div className="card-body">
                <h1>Settings page for {className.toUpperCase()}</h1>
                <Link to={{ pathname: "/", }}>Back home</Link>
                &nbsp;&nbsp;&nbsp;
                <a href="" onClick={() => firebase.auth().signOut()}>Sign-out</a>
              </div>
            </div>
            <Description/>
            { signedIn
              ? (
              <>
                <ManageAdmins classHash={instructorHash} db={db}
                              userEmail={userEmail}/>
                <UploadRoster classHash={instructorHash} db={db}/>
                <AddQuestions classCode={className} classHash={instructorHash} db={db}/>
              </>
              )
              : <></>
            }
          </div>
        </div>
      </div>
    </>
  )
}



export const Description = () => (
  <div className="card mt-4 mx-auto" style={{maxWidth: 800}}>
    <div className="card-body">
      <h2> Weekly Timeline </h2>
      <hr/>
      Here is what a week of survey would look like:
      <ul>
        <li>From <b>Monday~Friday,</b> your students will be asked to fill out the feedback form.</li>
        <li>On <b>Sunday,</b> you will receive a weekly digest from us along with all the feedback sampled from your students.</li>
        <li>Changes to survey questions (and the new roster) will be reflected around <b>11:59pm on Sundays</b>. Any change you make go live then. </li>
      </ul>
    </div>
  </div>
)

export const UploadRoster = (prop) => {
  const [csvFile, setCsvFile] = useState([])
  const [oldSuid, setOldSuid] = useState([])
  const [suid, setSuid] = useState([])
  const [oldNames, setOldNames] = useState([])
  const [names, setNames] = useState([])
  const [isDamaged, setIsDamaged] = useState(false)
  const [staged, setStaged] = useState(false)

  useEffect(() => {
    const classRef = doc(prop.db, 'rosters', prop.classHash)

    getDoc(classRef)
      .then((snap) => {
        const data = snap.data()
        setOldSuid(data.id)
        setOldNames(data.name)
      })
      .catch((error) => {
        console.log(error)
        ErrorMessage('Invalid access. Did you follow the correct URL?')
      })
  }, [])

  const onUpload = (csvFile) => {
    setIsDamaged(false)
    const defaultLen = csvFile[0].data.length
    const email_idx = csvFile[0].data.indexOf('SIS Login ID')
    const name_idx = csvFile[0].data.indexOf('Student')

    if (email_idx === -1 || name_idx === -1){
      ErrorMessage("Could not find 'Student' or 'SIS Login ID' columns. Make sure to upload a valid CSV file with both columns")
      return
    }

    let suid = []
    let names = []
    for (var i = 1; i < csvFile.length; i++) {
      if (csvFile[i].data.length != defaultLen) {
        ErrorMessage('The file seems to be broken. (Do all rows have the same length?)')
        setIsDamaged(true)
        return
      }
      const email = csvFile[i].data[email_idx]
      const stud_name = csvFile[i].data[name_idx]
      if (typeof email == 'undefined' 
          || typeof stud_name == 'undefined'
          || stud_name == 'Student, Test'
          || email.length === 0
          || stud_name.length === 0){
        continue
      }
      suid.push(email)
      names.push(stud_name)
    }
    setSuid(suid)
    setNames(names)
    setStaged(true)
  }

  const onClick = (event) => {
    if (isDamaged){
      ErrorMessage('The file seems to be broken. (Do all rows have the same length?)')
      return
    }
    if (!staged){
      ErrorMessage("Stage a new roster to upload!")
      return
    }

    const classRef = doc(prop.db, 'rosters', prop.classHash)
    setDoc(classRef, {'id': suid, 'name': names})
    .then((value) => { 
      SuccessMessage("Upload Complete!")
      setStaged(false)
      setOldSuid(suid)
      setOldNames(names)
    })
    .catch((error) => { 
      console.log(error)
      ErrorMessage("Invalid access. Are you using the correct URL?") })
  }

  return (
    <>
      <div className="card mt-4">
        <div className="card-body small-padding-card">
          <div className="question-spacing">
            <div className="question-spacing">
              <h2>Update Roster</h2>
              <hr/>
              <p>To update the roster for your class:</p>
              <ul>
                <li>Go to the "Grades" section in the class Canvas page</li>
                <li>Download the gradebook by clicking "Download Current Scores (.csv)"</li>
                <ul>
                  <li>If you don't see this button, you're in "Gradebook" mode. Look for the "Actions" tab and click "Export"</li>
                </ul>
                <li>Upload the downloaded gradebook here. (We only upload the SUID and the name fields.)</li>
              </ul>
              <p>
              You can remove private information like grades from the csv file, <b>but please keep the "Student" and "SIS Login ID"</b> columns intact.
              </p>

              <p style={{color: 'red'}}>
                <b><u>WARNING:</u></b> Please make sure to <b>review the uploaded roster and correct any errors</b> before uploading.
              </p>
              <CSVReader
                addRemoveButton
                config={{skipEmptyLines: true}}
                onDrop={onUpload}
                onError={(err, file, inputElem, reason)=>ErrorMessage(reason)}
                onRemoveFile={(data) => {
                  setStaged(false)
                  setSuid([])
                  setNames([])
                }}
              >
                <span>Drop CSV file here or click to upload.</span>
              </CSVReader>

              <div style={{'textAlign': 'center', 'color': (staged? 'blue': 'black')}}>
                {staged
                  ? `Total of ${suid.length} students staged for upload`
                  : `Current roster has ${oldSuid.length} students`}
                <div style={{'max-height': '300px', 'overflowY': 'scroll'}}>
                <Table>
                  <thead>
                    <tr>
                      <th> No. </th>
                      <th> SUNet ID </th>
                      <th> Name </th>
                    </tr>
                  </thead>
                  <tbody style={{'color': (staged?'blue':'black')}}>
                    {Array.from((staged? suid: oldSuid).keys()).map((i, _) => 
                      <tr>
                        <td> {i+1} </td>
                        <td> {(staged? suid: oldSuid)[i]} </td>
                        <td> {(staged? names: oldNames)[i]} </td>
                      </tr>
                    )}
                  </tbody>
                </Table>
                </div>
              </div>

              <Button onClick={onClick}>
                Upload!
              </Button>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
