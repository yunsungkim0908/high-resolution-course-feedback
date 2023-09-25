import React, { useRef, useState, useEffect } from 'react';
import { Table, Button ,Dropdown } from 'react-bootstrap'
import { doc, deleteDoc, updateDoc, setDoc, getDoc } from "firebase/firestore";
import { Formik, Form, useFormikContext, Field, useField, FieldArray } from 'formik';
import "../components/Forms/Form.css"
import "../feedback/feedback.css"
import { TextInputCell } from "../components/Forms/Form.js"
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faTrashAlt, faPlus } from '@fortawesome/free-solid-svg-icons'
import { ErrorMessage, SuccessMessage } from "../components/utils.js"
import * as Yup from "yup";
import { useHistory } from "react-router-dom";

const AddAdmin = ({admins, setAdmins, submit}) => {
  const [ newAdmin, newAdminMeta, newAdminHelpers ] = useField("newAdmin")
  const emailSchema = Yup.string().email()

  return (
    <tr>
      <td/>
      <td>
        <TextInputCell
          label="newAdmin"
          index="newAdmin"
          name="newAdmin"
          placeholder="Enter email"
        />
      </td>
      <td>
        <Button onClick={() => {
          if (emailSchema.isValidSync(newAdmin.value)){
            const newAdmins = [...admins, newAdmin.value]
            setAdmins(newAdmins)
            submit(newAdmins)
            newAdminHelpers.setValue("")
          } else {
            newAdminHelpers.setError("Invalid email")
          }
        }}>
          <FontAwesomeIcon icon={faPlus} />
        </Button>
      </td>
    </tr>
  )
}

const AdminRow = ({email, i, createdByEmail, userEmail, admins, setAdmins, submit}) => {
  let history = useHistory();

  return (
    <tr>
      <td>{i+1}</td>
      <td>{email}</td>
      <td>
        { (createdByEmail === email) 
          ? <>Owner</>
          : <Button variant="danger" onClick={() => {
              const newAdmins = admins.filter((e) => e !== email)
              setAdmins(newAdmins)
              submit(newAdmins)
              if (email === userEmail)
                history.push("/")
            }}>
              <FontAwesomeIcon icon={faTrashAlt} />
            </Button>
        }
      </td>
    </tr>
  )
}

export const ManageAdmins = (props) => {
  const [admins, setAdmins] = useState([])
  const [createdByEmail, setCreatedBy] = useState("")

  useEffect(() => {
    getDoc(doc(props.db, "courses", props.classHash))
      .then((snap) => {
        const adminLst = snap.data()["admins"]
        setCreatedBy(snap.data()["createdByEmail"])
        setAdmins(adminLst)})
      .catch((error) => {
        console.log(error)
        ErrorMessage("Cannot read course info. Have you logged in?")
      })
  }, [])

  const updateAdmins = (newAdmins) => {
    if (props.classHash != null){
      const courseDoc = doc(props.db, "courses", props.classHash)
      setAdmins(newAdmins)
      updateDoc(courseDoc, {"admins": newAdmins})
        .then(() => {SuccessMessage("Submitted!")})
        .catch((error) => {ErrorMessage("Submit failed. Have you logged in?")})
    } else {
      ErrorMessage("Invalid access. Did you follow the correct URL?")
    }
  }

  return (
    <div className="card mt-4 mx-auto" style={{maxWidth: 800}}>
      <div className="card-body">
        <h2> Manage Admins </h2>
        <hr/>
        <p>Add or remove admins by their email <span style={{"color": "red"}}>(@stanford.edu emails only)</span>. Admins will be able to:</p>
        <ul>
          <li>Edit the survey settings by logging in with the saved email address.</li>
          <li>Receive weekly survey digests through the same email address.</li>
        </ul>
          <div style={{'textAlign': 'center', 'max-height': '300px', 'overflowY': 'scroll'}}>
            <Table>
              <thead>
                <tr>
                  <th>No.</th>
                  <th>Email</th>
                  <th/>
                </tr>
              </thead>
              <tbody>
                {admins.map((email, i) => {
                  return <AdminRow i={i} email={email}
                          createdByEmail={createdByEmail}
                          userEmail={props.userEmail}
                          admins={admins} setAdmins={setAdmins}
                          submit={updateAdmins}/>})
                }
                <Formik initialValues={{newAdmin: null}}>
                  <AddAdmin admins={admins} setAdmins={setAdmins} submit={updateAdmins}/>
                </Formik>
              </tbody>
            </Table>
            {/*<Button type="submit" onClick={updateAdmins}>
              Save Changes
            </Button>*/}
          </div>
      </div>
    </div>
  )
}
