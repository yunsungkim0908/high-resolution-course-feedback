import React, { useEffect, useState } from 'react';
import { Table, Button ,Dropdown } from 'react-bootstrap'
import 'firebase/compat/auth';
import Swal from "sweetalert2";
import { Formik, Form } from 'formik';
import * as Yup from "yup";
import "../feedback/feedback.css"
import { TextInputCell } from "../components/Forms/Form.js"
import { ErrorMessage, SuccessMessage } from "../components/utils.js"
import { doc, collection, writeBatch, deleteDoc, updateDoc, addDoc, setDoc, getDoc } from "firebase/firestore";
import { ClassBeginsPicker, FirstWeekPicker, LastWeekPicker } from "../components/Forms/date.js"

const LabeledRow = ({label, ...props}) => {
  return (
    <tr>
      <td>
        <label className="form-label" style={{"textAlign": "right", "marginRight": "10px"}}>
          {label}
        </label>
      </td>
      <td>
        {props.children}
      </td>
    </tr>
  )
}

export const AddCourse = (props) => {
  const [userCourses, setUserCourses] = props.coursesState
  const [userCourseIds, setUserCourseIds] = props.courseIdState
  const [deselectToggle, setDeselectToggle] = useState(false)

  const createCourse = (db, newValues) => {
    const batch = writeBatch(db)

    const courseId = doc(collection(db, "courses")).id

    const newCourseIds = [...userCourseIds, courseId]
    const newCourses = [...userCourses, newValues]

    newValues["hash"] = courseId

    const courseRef = doc(db, "courses", courseId)
    const rosterRef = doc(db, "rosters", courseId)
    const questionRef = doc(db, "questions", courseId)

    const write = async () => {
      batch.set(courseRef, newValues)
      batch.set(questionRef, {"previous-questions": [], "questions": []})
      batch.set(rosterRef, {"id": [], "name": []})
      return batch.commit()
    }

    write()
      .then(() => {
        setUserCourseIds(newCourseIds)
        setUserCourses(newCourses)
        SuccessMessage(`Submitted! Please email the HRCE admin with the following courseId for approval:\n${courseId}`)
      })
      .catch((error) => {console.log(error)})
  }

  const initialValues = {
    courseName: "",
    callNumber: "",
    numQuery: 2,
    numWeeks: 0,
    firstWeek: "",
    lastWeek: "",
    classBegins: ""
  }

  const validationSchema = Yup.object().shape({
    courseName: Yup.string().required("Required"),
    callNumber: Yup.string().required("Required"),
    numQuery: Yup.number().integer("Integer only")
      .positive("Invalid count").required("Required"),
    numWeeks: Yup.number().integer("Integer only").typeError('Invalid first/last weeks')
      .positive('Invalid first/last weeks').required('Required'),
    firstWeek: Yup.string().required("Required"),
    lastWeek: Yup.string().required("Required"),
    classBegins: Yup.string().required("Required")
  });

  const onSubmit = (newValues) => {
    const courseExists = (e) => {
      return (e.callNumber === newValues.callNumber)
    }

    if (userCourses.some(courseExists)){
      ErrorMessage("A course with the same call number already exists.")
      return
    }

    newValues["completed"] = 0
    newValues["admins"] = [props.user.email]
    newValues["createdBy"] = props.user.uid
    newValues["createdByEmail"] = props.user.email
    newValues["numQuery"] = parseInt(newValues.numQuery)

    createCourse(props.db, newValues)
  }

  const render = (props) => {
    return (
      <Form>
        <table><tbody>
          <LabeledRow label="Call Number">
              <TextInputCell
                label='Call Number'
                index='callNumber'
                name='callNumber'
                placeholder='e.g., CS101, COMS101'
              />
          </LabeledRow>
          <LabeledRow label="Course Name">
              <TextInputCell
                label='Course Name'
                index='courseName'
                name='courseName'
                placeholder='e.g., Intro to Programming'
              />
          </LabeledRow>
          <LabeledRow label="Surveys per Student">
              <TextInputCell
                label='Surveys per Student'
                index='numQuery'
                name='numQuery'
                placeholder='Enter number'
              />
          </LabeledRow>
          <LabeledRow label="First Week of Classes">
            <ClassBeginsPicker deselectToggle={deselectToggle}/>
          </LabeledRow>
          <LabeledRow label="First Week of Survey">
            <FirstWeekPicker deselectToggle={deselectToggle}/>
          </LabeledRow>
          <LabeledRow label="Last Week of Survey">
            <LastWeekPicker deselectToggle={deselectToggle}/>
          </LabeledRow>
          <LabeledRow label="Number of Weeks">
              <TextInputCell
                disabled={true}
                label='Number of Weeks'
                index='numWeeks'
                name='numWeeks'
                placeholder='Enter number'
              />
          </LabeledRow>
        </tbody></table>
        <div>
          <Button type="submit" variant="primary">
            Create
          </Button>
          <Button type="reset" variant="secondary" className=""
            onClick={()=>{
              props.resetForm();
              setDeselectToggle(!deselectToggle)}}
          >
            Reset
          </Button>
        </div>
      </Form>
    )
  }

  return (
    <div>
    <div className="card mt-4 mx-auto" style={{maxWidth: 800}}>
    <div className="card-body">
      <h2> Create a course survey</h2>
      <hr/>
      <p>Create a course survey by filling in the following information and clicking "Create." Once you create a course survey, go to the course settings link in "Your Courses" to finish setting up the survey.</p>

      <h5><b><u>Note</u></b></h5>
      <ol>
        <li>Once created, the course info <span style={{color: "red"}}><b>cannot be edited</b></span>. If you made a mistake, you must <u>permanently delete</u> that survey and create a new one.</li>
        <li>Make sure to <span style={{color: "red"}}><b>avoid creating duplicate</b></span> surveys for the same course!</li>
        <li>After you create a course, please make sure to <span style={{color: "red"}}><b>email the course ID</b></span> to the HRCE admin to get the course approved for survey.</li>
      </ol>

      <h5><b><u>Fields</u></b></h5>
      <ul>
        <li><b>Call Number:</b> Course call number that will show up in the survey emails sent to students</li>
        <li><b>Course Name:</b> Name of your course</li>
        <li><b>Surveys per Student:</b> Each student is surveyed exactly this number of times in total.</li>
        <li><b>First Week of Classes:</b> Used to track weeks throughout the survey.</li>
        <li><b>First Week of Survey:</b> The first survey will be sent out on the Monday of the chosen week.
          <br/> (Note: Survey should begin after the <span style={{color: 'red'}}>2nd week</span> of the course.)</li>
        <li><b>Last Week of Survey:</b> The last survey will be sent out on the Monday of the chosen week.</li>
      </ul>

      <div className="center" style={{width: 400}}>
        <Formik
          validateOnChange={false}
          validateOnBlur={false}
          initialValues={initialValues}
          validationSchema={validationSchema}
          enableReinitialize={true}
          onSubmit={onSubmit}
          render={ render }
        />
      </div>
    </div>
    </div>
    </div>
  )
}
