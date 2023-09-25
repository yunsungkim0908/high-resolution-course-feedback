import React, { useEffect, useState } from 'react';
import { Table, Button ,Dropdown } from 'react-bootstrap'
import { collection, doc, query, getDocs, where,
  writeBatch, updateDoc, setDoc, getDoc } from "firebase/firestore";
import 'firebase/compat/auth';
import Swal from "sweetalert2";
import * as Yup from "yup";
import "../feedback/feedback.css"
import { truncateString, ErrorMessage, SuccessMessage } from "../components/utils.js"
import { Link, useLocation } from "react-router-dom";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faPauseCircle, faCheckCircle, faCopy, faPencilAlt, faTrashAlt, faMinus } from '@fortawesome/free-solid-svg-icons'

const CourseRow = ({course, ...props}) => {
  const [courses, setCourses] = props.coursesState
  const [courseIds, setCourseIds] = props.courseIdState
  const [approvalStatus, setApprovalStatus] = useState(undefined)
  const courseId = course["hash"]
  const db = props.db

  const deleteCourse = async () => {
    const batch = writeBatch(db)
    const courseId = course.hash

    const courseRef = doc(db, "courses", courseId)
    const rosterRef = doc(db, "rosters", courseId)
    const questionRef = doc(db, "questions", courseId)

    const newCourseIds = courseIds.filter((e) => e !== courseId)
    const newCourses = courses.filter((e) => e.callNumber !== course.callNumber)

    const write = async () => {
      batch.delete(rosterRef)
      batch.delete(questionRef)
      batch.delete(courseRef)
      return batch.commit()
    }

    Swal.fire({
      title: (
        '<span style="color: red"><u>Warning</u>: </span>You are about to <u>permanently delete</u> a course. '+
        "This action cannot be undone. Are you sure?"), 
      showCancelButton: true,
      confirmButtonText: "Yes, delete permanently",
      cancelButtonText: "No, cancel"
    }).then((result) => {
      if (result.isConfirmed) {
        write()
          .then(() => {
            setCourseIds(newCourseIds)
            setCourses(newCourses)
            SuccessMessage("Done!")
          .catch((error) => {console.log(error)})
          })
      } else {
        Swal.fire("Changes are not saved")
      }
    })
  }

  useEffect(() => {
    const approvedDoc = doc(db, 'approvedCourses', courseId)
    getDoc(approvedDoc)
      .then((snap) => { setApprovalStatus(snap.exists()) })
      .catch((error) => { console.log(error) })
  },[course.hash])

  const StatusLabel = () => {
    if (approvalStatus === undefined)
      return <></>
    if (approvalStatus)
      return (
        <div>
          <FontAwesomeIcon color="green" icon={faCheckCircle}/>
          <br/>
          Approved
        </div>
      )
    else
      return (
        <div>
          <FontAwesomeIcon color="gold" icon={faPauseCircle}/>
          <br/>
          Pending Approval
        </div>
      )
  }

  const courseNameTrunc = truncateString(course["courseName"], 12) 
  const callNumberTrunc = truncateString(course["callNumber"], 12) 

  const [showId, setShowId] = useState(false)

  const IdLabel = ({fullCourseId}) => (
      <label style={{textDecoration: showId ? "underline" : "",
                    color: showId ? "blue" : "",
                    width: 80}}
        onMouseOver = {() => {setShowId(true)}}
        onMouseOut = {() => {setShowId(false)}}
        onClick={(event) => {
          navigator.clipboard.writeText(fullCourseId)
          SuccessMessage(`Course Id: ${fullCourseId}\nCopied to clipboard!`)
        }}
      >
        <FontAwesomeIcon icon={faCopy} size="xs"/>
        {fullCourseId}
        {/*{showId ? fullCourseId : truncateString(fullCourseId, 12)}*/}
      </label>
    )

  return(
    <tr key={course["hash"]}>
      <td className="align-middle"> <IdLabel fullCourseId={course["hash"]}/> </td>
      <td className="align-middle"> 
        <Link to={{
            pathname: "course",
            search: `?callNumber=${course["callNumber"]}&classHash=${course["hash"]}`
          }}>
          {callNumberTrunc}
        </Link>
      </td>
      <td className="align-middle"> {courseNameTrunc} </td>
      <td className="align-middle"> {course["firstWeek"]} </td>
      <td className="align-middle"> {course["lastWeek"]} </td>
      <td className="align-middle"> {approvalStatus ? `${course["completed"]}/${course["numWeeks"]}` : ""} </td>
      <td className="align-middle"> <StatusLabel/> </td>
      <td className="align-middle">
        <div>
          <Link to={{
              pathname: "course",
              search: `?callNumber=${course["callNumber"]}&classHash=${course["hash"]}`
            }}>
            <Button>
              <FontAwesomeIcon icon={faPencilAlt} size="sm"/>
            </Button>
          </Link>

          {/*<Button variant="warning" onClick={removeCourse}>
            <FontAwesomeIcon icon={faMinus} size="xs"/>
            </Button>*/}
          { (props.user.uid === course["createdBy"])
            ? <Button variant="danger" onClick={deleteCourse}>
                <FontAwesomeIcon icon={faTrashAlt} size="sm"/>
              </Button>
            : <></>
          }
        </div>
      </td>
    </tr>
  )
}

export const CoursesTable = (props) => {
  const [userCourses, setUserCourses] = props.coursesState
  const [userCourseIds, setUserCourseIds] = props.courseIdState
  const [courseLoaded, setCourseLoaded] = useState(false)
  const user = props.user

  useEffect(() => {
    if (!user){
      return (
        <p> You must login </p>
      )
    }

    const coursesRef = collection(props.db, "courses")
    const q = query(coursesRef, where("admins", "array-contains", user.email))
    getDocs(q)
      .then((qSnap) => {
        const newCourseIds = qSnap.docs.map((snap) => snap.data()["hash"])
        const newCourses = qSnap.docs.map((snap) => snap.data())
        setUserCourseIds(newCourseIds)
        setUserCourses(newCourses)
        setCourseLoaded(true)
      })
  }, [])

  if (!courseLoaded)
    return (
      <div>
      <div className="card mt-4 mx-auto" style={{maxWidth: 800}}>
      <div className="card-body">
        <h2> Your courses </h2>
        <hr/>
        <p> Loading... </p>
      </div>
      </div>
      </div>
    )

  return (
    <div>
    <div className="card mt-4 mx-auto" style={{maxWidth: 800}}>
    <div className="card-body">
      <h2> Your courses </h2>
      <hr/>
      <p>Here is a list of courses of which you are an admin. You can change the weekly survey settings (e.g., update rosters, update weekly questions, manage admins) by clicking the link to the survey settings page.</p>

      <h5><b><u>Note</u></b></h5>
      <ul>
        <li>To become an admin of an existing course survey, one of the existing admins (including the owner) must add you manually.</li>
        <li>Please <span style={{color: "red"}}><b>email the course ID</b></span> to the HRCE admin to get the course approved for survey.</li>
        <li><FontAwesomeIcon icon={faPencilAlt} size="sm"/>: Go to settings page and edit admins, rosters, and survey questions</li>
        <li><FontAwesomeIcon icon={faTrashAlt} size="sm"/> (Owners only): <span style={{color: "red"}}>Permanently delete</span> the course survey.</li>
      </ul>

      <Table>
        <thead style={{textAlign: "center"}} >
          <tr>
            <th> Course Id </th>
            <th> Call Number </th>
            <th> Course Name </th>
            <th> First Survey {"\n"} (Week of)</th>
            <th> Last Survey {"\n"} (Week of)</th>
            <th> Survey Progress </th>
            <th> Status </th>
            <th> Actions </th>
          </tr>
        </thead>
        { userCourses.length === 0
          ? <></>
          : <tbody style={{textAlign: "center"}} >
              {userCourses.map((course) =>
                <CourseRow course={course} 
                  coursesState={props.coursesState}
                  courseIdState={props.courseIdState}
                  db={props.db} user={props.user}/>)}
            </tbody>
        }
      </Table>
      { userCourses.length === 0
        ? <div style={{textAlign: "center"}}>
            <label>No items to display</label>
          </div>
        : <></>
      }
    </div>
    </div>
    </div>
  )
}

