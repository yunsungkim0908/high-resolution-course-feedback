
import { Button, ButtonGroup, Dropdown } from "react-bootstrap";
import ToggleButton from 'react-bootstrap/ToggleButton'
import React, { useState, useEffect } from 'react';
// import firebase from "firebase";
import "bootstrap/dist/css/bootstrap.min.css";
import "./feedback.css"
import { Form, Formik, FieldArray, useField } from "formik";
import * as Yup from "yup";
import { firebaseConfig } from "../firebase/config";
import {TextAreaInputCard, TextInputCard, StarsInput, RadioInput} from "../components/Forms/Form.js"
import firebase from 'firebase/compat/app';
import { initializeApp } from 'firebase/app';
import { getFirestore, collection, getDocs } from 'firebase/firestore';
import { doc, setDoc, getDoc } from "firebase/firestore";
import Swal from "sweetalert2";
import { Link, useLocation } from "react-router-dom";

import { getAuth, onAuthStateChanged } from 'firebase/auth';

// A custom hook that builds on useLocation to parse
// the query string for you.
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
      title: errorMsg
    })
}

const getPlaceholder = function(question) {
  switch (question.type) {
    case 'Text': return 'Write text here.'
    case 'Numeric': return 'Write number here.'
    default: return ''
  }
}

export const QuestionBox = ({question, index}) => {
  switch (question.type) {
    case 'Text':
    case 'Numeric':
      return <TextInputCard
        label={question.prompt}
        name={`answers[${question.qid}]`}
        index={index}
        placeholder={('placeholder' in question) 
                      ? question.placeholder
                      : getPlaceholder(question)}
        type='text'
      />
    case 'Rating (1-5)':
    case 'Rating (Qualitative)':
      return <ButtonInput question={question} index={index}/>
    default:
      return <></>
  }
}

export const SurveyPage = (prop) => {
  const [questions, setQuestions] = useState({'questions': [], 'classWeek': ""})
  const [invalidURL, setInvalidURL] = useState(false)
  const [isPreview, setIsPreview] = useState(false)

  let queryParams = useQuery();
  let callNumber = queryParams.get('callNumber')
  const classHash = queryParams.get('classHash')
  let globalWeek = queryParams.get('week')
  let userHash = queryParams.get('user') 

  const [closed, setClosed] = useState(false)

  const db = prop.db

  const readDocAndDo = function(docRef, doSomething){
    return getDoc(docRef)
      .then((snap) => { 
        if (typeof snap.data() == 'undefined')
          throw new Error('The survey has been closed, or the URL you entered is invalid. Did you follow the correct URL?')
        else
          {return doSomething(snap)}})
      .catch((error) => {
        ErrorMessage(error.message)
      })
  }

  useEffect(() => {
    if(!classHash || !userHash) {
      setInvalidURL(true)
      return
    } else if (userHash === 'preview') {
      setIsPreview(true)
      const auth = getAuth()
      onAuthStateChanged(auth, (user) => {
        const defaultQuesRef = doc(db, 'shared', 'defaultQuestions')
        const customQuesRef = doc(db, 'questions', classHash)
        Promise.all([
          readDocAndDo(defaultQuesRef, (snap) => snap.data().questions),
          readDocAndDo(customQuesRef, (snap) => snap.data().questions)
        ]).then((values) => {
          const qlist = values[0].concat(values[1])
          setQuestions({'questions': qlist})
        })
      })
    } else {
      if (!globalWeek)
        setInvalidURL(true)
      readDocAndDo(
        doc(doc(db, 'surveyQuestions', globalWeek), classHash, userHash),
        (snap) => {
          if (snap.data().questions === 'closed')
            setClosed(true)
          else
            setQuestions(snap.data())
        }
      )
    }
  }, [])

  if (invalidURL) { return <h1>Invalid URL</h1>}

  
  const initValues = {answers: {}}
  questions.questions.map((question, index) => 
    {initValues.answers[question.qid] = ''}
  )

  const valShape = {}
  questions.questions.map((question, index) => {
    let val
    switch (question.type) {
      case 'Text':
        val = Yup.string().required('Required')
        break
      case 'Numeric':
        val = Yup.number().typeError('Answer must be a number').required("Required")
        break
      case 'Rating (1-5)':
      case 'Rating (Qualitative)':
        val = Yup.string().required("Required")
        break
      default:
        val = null
    }
    valShape[question.qid] = val
  })
  const validationSchema = Yup.object().shape({
    answers: Yup.object().shape(valShape)
  });

  const onSubmit = function(newValue) {
    var d = new Date()
    newValue['course'] = classHash
    newValue['timestamp'] = d.toUTCString()
    if (isPreview || closed)
      return
    if (classHash != null && userHash != null) {
      const courseAnswersRef = doc(
        doc(db, "surveyAnswers", globalWeek), classHash, userHash
      )
      const courseQuestionsRef = doc(
        doc(db, "surveyQuestions", globalWeek), classHash, userHash
      )
      getDoc(courseQuestionsRef)
      .then((snap) => {
        if (snap.data().questions === 'closed'){
          ErrorMessage("Survey for this week has been closed.")
        } else {
          setDoc(courseAnswersRef, newValue)
          .then((value) =>
                {SuccessMessage("Submitted!") })
          .catch((value) =>
                {ErrorMessage("Invalid access. Either the survey has closed, or the URL is incorrect.")})
        }
      })
    }
  }

  const classWeek = ("classWeek" in questions) ? questions["classWeek"] : ""

  const header = isPreview? `Preview Survey Page for ${callNumber.toUpperCase()}` : `Week ${classWeek} Feedback for ${callNumber.toUpperCase()}`
  const desc = (isPreview
    ? 'This is a preview of the survey page that your students would get to see. Clicking the submit button doesn\'t do anything.'
    : 'In '+callNumber.toUpperCase()+', we will use a small amount of student feedback each week to infer higher resolution information on how the class is going. Thank you for your time!')

  /**
   * Stop enter submitting the form.
   * @param keyEvent Event triggered when the user presses a key.
   */
  function onKeyDown(keyEvent) {
    if ((keyEvent.charCode || keyEvent.key) === "Enter") {
      keyEvent.preventDefault();
    }
  }


  return (
    <>
      <div className="container">
        <div className="row">
          <div className="col">
            <div className="card mt-4 mx-auto" style={{maxWidth: 800}}>
              <div className="card-body">
                <h1>{header}</h1>
                <p>{desc}</p>
                {isPreview &&
                <p>
                  <Link
                    to={{
                      pathname: "/course",
                      search: `?callNumber=${callNumber}&classHash=${classHash}&user=preview`
                  }}>
                    Go back
                  </Link>
                </p>}
              </div>
            </div>
            
            
            <Formik
              validateOnChange
              enableReinitialize={true}
              initialValues={initValues}
              validationSchema={validationSchema}
              onSubmit={(x) => onSubmit(x)}
            >
              <Form onKeyDown={onKeyDown} style={{ width: "100%" }}>
                <FieldArray
                  name="answers"
                  render={() => 
                    {
                      if (closed) {
                        return (
                          <div className="card mt-4">
                          <div className="card-body" >
                            <p style={{'fontSize':'1.2rem'}}>We're sorry, but this week's survey has been closed.</p>
                          </div>
                          </div>
                        )
                      } else {
                        return (questions.questions.map((question, index) =>
                        <QuestionBox question={question} index={index}/>))
                    }
                   }
                  }
                />
                <div className="card mt-4 mx-auto" style={{maxWidth: 800}}>
                  <div className="card-body">
                    <Button 
                      variant="primary" 
                      type="submit" 
                      className="mx-auto"
                      disabled={questions.questions.length === 0}
                    >
                       Submit my feedback!
                    </Button>
                  </div>
                </div>
              </Form>
            </Formik>
          </div>
        </div>
      </div>
    </>
  );
};

const ButtonInput = ({question, index}) => {
  const [radioValue, setRadioValue] = useState('');
  const [field, meta, helpers] = useField(`answers.${question.qid}`)

  let radios
  switch (question.type) {
    case 'Rating (1-5)':
      // radios = ['5', '4', '3', '2', '1']
      radios = ['1', '2', '3', '4', '5']
      break
    case 'Rating (Qualitative)':
      // radios = ['Excellent', 'Good', 'Ok', 'Below Average', 'Poor']
      radios = ['Poor', 'Below Average', 'Ok', 'Good', 'Excellent']
      break
    default:
      radios = []
  }
  
  return <>
    <div className="card mt-4">
    <div className="card-body" >
      <p style={{'fontSize':'1.2rem'}}><b>{index+1}. </b>{question.prompt}</p>
      <ButtonGroup>
        {radios.map((radio, idx) => (
          <ToggleButton
            key={idx}
            id={`radio-${idx}`}
            type="radio"
            variant={'outline-primary'}
            name="radio"
            value={radio}
            checked={radioValue === radio}
            onChange={(e) => {
              setRadioValue(e.currentTarget.value)
              helpers.setValue(e.currentTarget.value)
            }}
            className='radio-button-fixed'
          >
            {radio}
          </ToggleButton>
        ))}
      </ButtonGroup>
      {meta.touched && meta.error && 
      <div className="error-space">
        <span className="error">{meta.error}</span>
      </div>}
    </div>
  </div>
  </>
}
