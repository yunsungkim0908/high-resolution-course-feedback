import React, { useRef, useState, useEffect } from 'react';
import { Table, Button ,Dropdown } from 'react-bootstrap'
import { Formik, Form, useFormikContext, Field, useField, FieldArray } from 'formik';
import "../components/Forms/Form.css"
import { doc, deleteDoc, updateDoc, setDoc, getDoc } from "firebase/firestore";
import Swal from "sweetalert2";
import * as Yup from "yup";
import { Link, useLocation } from 'react-router-dom'
import TextareaAutosize from 'react-textarea-autosize';
import autosize from 'autosize'


const choices = [
  'Text',
  'Numeric',
  'Rating (1-5)',
  'Rating (Qualitative)'
]

const ErrorMessage = (errorMsg) => {
    Swal.fire({
      icon: "error",
      title: errorMsg
    })
}

export const QuestionTypeDropdown = ({index, questions, freezeQues}) => {
  const questionType = questions[index].type
  const selection = (questionType == "")? 'Please Choose' : questionType
  const [field, meta, helpers] = useField(`questions.${index}.type`)

  return (
    <>
      <Dropdown>
        <Dropdown.Toggle variant="outline-primary" id="dropdown-basic">
          {selection}
        </Dropdown.Toggle>

        <Dropdown.Menu>
          {
            choices.map((choice, idx) => (
              <Dropdown.Item 
                key={idx}
                onClick = {() => {
                  helpers.setValue(choice)
                }}
                disabled={freezeQues} 
              >{choice}</Dropdown.Item>
            ))
          }
        </Dropdown.Menu>
      </Dropdown>
      {meta.touched && meta.error && 
      <div className="error-space">
        <span className="error">{meta.error}</span>
      </div>}
    </>
  )
}
//
// Table row for custom questions customized by teachers.
export const EditableRow = ({index, arrayHelpers, questions, freezeQues}) => {
  const [promptField, promptMeta]= useField(`questions.${index}.prompt`)
  const { submitForm } = useFormikContext()

  return (
    <>
      <tr key={index}>
        <th>
          <TextareaAutosize className="text-area-input" disabled={freezeQues}
            {...promptField}/>
          {promptMeta.touched && promptMeta.error &&
          <p>
            <span className="error">{promptMeta.error}</span>
          </p>}
        </th>
        <th>
          <QuestionTypeDropdown index={index} questions={questions} freezeQues={freezeQues}/>
        </th>
        <th width='110px'>
          <Button variant="danger" type="button" disabled={freezeQues}
            onClick={() => {
              arrayHelpers.remove(index)
              submitForm()
            }}>
           Delete
          </Button>
        </th>
      </tr>
    </>
  )
}

// First rows are populated by the default questions, followed by
// custom ones. The table initially displays the previous customized questions
export const QuestionsTable = (props) => {
  const [defaultQues, setDefaultQues] = useState([])
  const [customQues, setCustomQues] = useState({'questions': [], 'previous-questions': []})
  const [prevCustomQues, setPrevCustomQues] = useState([])
  const [freezeQues, setFreezeQues] = useState(false)

  useEffect(() => {
    getDoc(doc(props.db, "shared", "default-questions"))
      .then((snap) => { setDefaultQues(snap.data()) })
      .catch((error) => {
        console.log(error)
        ErrorMessage(error)
        return
      })
  }, []) 

  useEffect(() => {
    getDoc(doc(props.db, "questions", props.classHash))
      .then((snap) => {
        if (typeof snap.data() == 'undefined')
          Swal.fire({
            icon: "error",
            title: 'Invalid access. Did you follow the correct URL?',
            showCancelButton:false,
            showConfirmButton:false,
            allowOutsideClick: false
          })
        else if ('questions' in snap.data() && 'previous-questions' in snap.data()){
          setCustomQues(snap.data())
          setPrevCustomQues(snap.data()['previous-questions'])}
        else
          throw new Error('No questions field. Please contact admin.')
      })
      .catch((error) => {
        console.log(error)
        ErrorMessage(error.message)
        return
      })
  }, []) 

  const toggleFreeze = (event) => {
    setFreezeQues(event.target.checked)
    if (event.target.checked)
      setCustomQues(prevCustomQues)
  }

  const render = ({values}) => {
    return (

    <Form>
      <FieldArray
        name="questions"
        render={arrayHelpers => (
          <div> 
            <Table>
              <thead>
                <tr>
                  <th>Question Prompt</th>
                  <th>Question Type</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
               {values.questions.map((_, index) => (
                 <EditableRow index={index} arrayHelpers={arrayHelpers}
                 questions={values.questions} freezeQues={freezeQues}/>
               ))}
              </tbody>
            </Table>
            {/*<div>
              <label> 
              <input type="checkbox" id="reuse-old"
                onChange={toggleFreeze}/> &nbsp;&nbsp;
                "Use the same questions from last week."</label>
            </div>*/}
            <Button type="button"
              onClick={() => {
                arrayHelpers.push({ prompt: '', type: '' })
              }}>
              Add Question
            </Button>
            <Button 
              type="submit" 
              className="mx-auto"
              
            >
              Save
            </Button>
          </div>
        )}
      />
    </Form>
    )
  }

  const onSubmit = (newValues) => {
    newValues['questions'].map((values, index) => {
      values['qid'] = `custom${index}`
    })

    if(props.classHash != null){
      const classQuesDoc = doc(props.db, 'questions', props.classHash)
      setDoc(classQuesDoc, newValues)
        .then(() => {
          Swal.fire({
            icon: "success",
            title: "Submitted!",
          })})
        .catch(() => {
          Swal.fire({
            icon: "error",
            title: "Invalid access. Did you follow the correct URL?",
          })})
    } else {
      Swal.fire({
        icon: "error",
        title: "Invalid access. Did you follow the correct URL?",
      })
    }
  }

  const validationSchema = Yup.object().shape({
    questions: Yup.array().of(
      Yup.object().shape({
        prompt: Yup.string().min(10, 'Too short (>10 chars)').required("Required"),
        type: Yup.string().required("Required")
      })
    )
  });

  return (
    <>
      <div>
          <p>You can ask more questions to your students in addition to our default questions. Modify your question prompts through this form and <b> click "Save" to save <span style={{color: 'red'}}> any </span> changes that you made</b>. <u>(Unless specifically deleted, the same questions from the previous week will be used.)</u></p>
        Choose one the following types for each question:
        <ul>
          <li><b>Text:</b> Students will give you a text response.</li>
          <li><b>Numeric:</b> Students will give you numeric answers.</li>
          <li><b>Rating (1-5):</b> Students will choose an integer rating from 1 to 5.</li>
          <li><b>Rating (Qualitative):</b> Students will choose from (Poor, Below Average, Ok, Good, Excellent).</li>
        </ul>
        <p>
          <Link
            to={{
              pathname: "/survey",
              search: `?callNumber=${props.classCode}&week=&classHash=${props.classHash}&user=preview`,
              state: {defaultQues: defaultQues,
                      customQues: customQues}
          }}>
            Preview
          </Link>
          {' '} of what your students would see in the next survey.
        </p>
        <p style={{color: 'red'}}>
          Note: Changes made now will be reflected to the survey between 0am~2am every Monday.
        </p>
        <Formik
          validateOnChange
          initialValues={customQues}
          validationSchema={validationSchema}
          enableReinitialize={true}
          onSubmit={onSubmit}
          render={ render }
        />
      </div>
    </>
  )
}

export const AddQuestions = (props) => {
  return (
    <>
      <div className="card mt-4">
        <div className="card-body small-padding-card">
          <div className="question-spacing">
            <div className="question-spacing">
              <h2>(Optional) Custom Questions of the Week</h2>
              <hr/>
              <QuestionsTable {...props}/>
            </div>
          </div>
        </div>
      </div>
    </>
  )
};


