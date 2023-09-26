import React from "react";
import { Field, useField } from "formik";
import "bootstrap/dist/css/bootstrap.min.css";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faStar,
} from "@fortawesome/free-solid-svg-icons";
import { faStar as faEmptyStar } from "@fortawesome/free-regular-svg-icons";
import "./Form.css";

export const TextInputCell = ({ label, ...props }) => {
  const [field, meta] = useField(props);

  return (
    <div>
      <input className="text-input" {...field} {...props} />
      {meta.error &&
        <div className="error-space">
         <span className="error">{meta.error}</span>
        </div>
      }
    </div>
  )
}

export const TextInputCard = ({ label, ...props }) => {
  const [field, meta] = useField(props);
  let description = props.description ? props.description : "";
  let descriptionDiv =
    description === "" ? (
      <span />
    ) : (
      <div className="description">{description}</div>
    );
  return (
    <div className="card mt-4">
      <div className="card-body small-padding-card" >
        <div className="question-spacing">
          <label className="form-label" htmlFor={props.id || props.name}>
            <b>{props.index+1}. </b>{label}
          </label>
          {descriptionDiv}

          <input className="text-input" {...field} {...props} />
          {meta.touched && meta.error &&
            <div className="error-space">
             <span className="error">{meta.error}</span>
            </div>
          }
        </div>
      </div>
    </div>
  );
};

export const StarsInput = (props) => {
  const [field, meta] = useField(props);
  return <>
    <div className="card mt-4">
      <div className="card-body small-padding-card" >
        <Field name={props.name} id={props.name} type="number">
          {({ field: { value }, form: { setFieldValue } }) => (
            <div>
              <label htmlFor={props.name} className={"form-label"}>
                {props.title}
              </label>
              <div className="mt-2">
                <Stars
                  count={value}
                  handleClick={(number) => setFieldValue(props.name, number)}
                />
                <i className="star-label">{value} / 5</i>
              </div>
            </div>
          )}
        </Field>
        <div className='error-space'>
        {meta.touched && meta.error && <span className="error">{meta.error}</span>}
        </div>
      </div>
    </div>
  </>
}

export const TextAreaInput = ({ label, ...props }) => {
  const [field, meta] = useField(props);

  return (
    <div className="question-spacing">
      <label className="question-label" htmlFor={props.id || props.name}>
        {label}
      </label>
      <div style={{ color: "gray", marginBottom: "0.6rem" }}>
        {props.description ? props.description : ""}
      </div>

      <Field
        className="text-area-input"
        as="textarea"
        rows="10"
        {...field}
        {...props}
      />
      <p>
      {meta.touched && meta.error && <span className="error">{meta.error}</span>}
      </p>
    </div>
  );
};
// <p>

export const TextAreaInputCard = ({ label, ...props }) => {
  const [field, meta] = useField(props);
  let description = props.description ? props.description : "";
  let descriptionDiv =
    description === "" ? (
      <span />
    ) : (
      <div className="description">{description}</div>
    );
  return (
    <div className="card mt-4">
      <div className="card-body small-padding-card" >
        <div className="question-spacing">
          <label className="form-label" htmlFor={props.id || props.name}>
            <b>{props.index+1}. </b>{label}
          </label>
          {descriptionDiv}

          <input className="text-area-input" {...field} {...props} />
          {meta.touched && meta.error &&
            <div className="error-space">
             <span className="error">{meta.error}</span>
            </div>
          }
        </div>
      </div>
    </div>
  );
};

export const RadioInput = ({ label, ...props }) => {
  return (
    <div className="class-spacing">
      <label className="question-label" htmlFor={props.id || props.name}>
        {label}
      </label>

      <div className="btn-group-toggle" data-toggle="buttons">
        <Field type="radio" name="rating" value="1" /> 1
        <Field type="radio" name="rating" value="2" /> 2
        <Field type="radio" name="rating" value="3" /> 3
        <Field type="radio" name="rating" value="4" /> 4
        <Field type="radio" name="rating" value="5" /> 5
      </div>

    </div>
  );
}

export const DescriptionField = ({ label, ...props }) => {
  let description = props.description ? props.description : "";
  let descriptionDiv =
    description === "" ? (
      <span />
    ) : (
      <div className="description">{description}</div>
    );
  return (
    <div>
      <label className="form-label" htmlFor={props.id || props.name}>
        {label}
      </label>
      {descriptionDiv}
    </div>
  );
};

export const SelectInput = ({ label, ...props }) => {
  const [field, meta] = useField({ ...props, type: "select" });

  return (
    <div className="question-spacing">
      <label className="question-label" htmlFor={props.id || props.name}>
        {label}
      </label>
      <div className="description">
        {props.description ? props.description : ""}
      </div>

      <Field as="select" className="select-input" {...field} {...props}>
        {props.children}
      </Field>
      {meta.touched && meta.error && <div className="error">{meta.error}</div>}
    </div>
  );
};

export const MultipleCheckbox = (props) => {
  /* eslint-disable no-unused-vars */
  const [field, meta] = useField({ ...props });
  /* eslint-enable no-unused-vars */
  const msg = props.description ? props.description : "Select all that apply";

  return (
    <div className="question-spacing" style={props.style}>
      <label className="form-label">{props.label}</label>
      <div className="description">{msg}</div>
      {props.children}
      {meta.touched && meta.error && <div className="error">{meta.error}</div>}
    </div>
  );
};

export const AgreeCheckbox = (props) => {
  /* eslint-disable no-unused-vars */
  const [field, meta] = useField({ ...props });
  /* eslint-enable no-unused-vars */
  return (
    <div className="question-spacing">
      <label className="form-label">{props.label}</label>
      <div style={{ color: "gray", marginBottom: "0.6rem" }}>
        {props.description ? props.description : ""}
      </div>

      {props.children}
      {meta.touched && meta.error && <div className="error">{meta.error}</div>}
    </div>
  );
};

export const Checkbox = (props) => {
  /* eslint-disable no-unused-vars */
  const [field, meta] = useField({ ...props });
  /* eslint-enable no-unused-vars */
  return (
    <div className="checkbox">
      <label className="form-label">
        <Field type="checkbox" {...props} />
        {props.label}
      </label>
    </div>
  );
};


/* Private helper */

const Star = ({ checked, onClick }) => (
  <span className="star" onClick={onClick}>
    {renderStar(checked)}
  </span>
);

const Stars = ({ count, handleClick }) => (
  
  <span className="stars">
    {[1, 2, 3, 4, 5].map((rating) => (
      <Star
        key={rating}
        checked={rating !== 0 && rating <= count}
        onClick={() => handleClick(rating)}
      />
    ))}
  </span>
);

Stars.defaultProps = {
  count: null,
  handleClick: (e) => e,
};

const renderStar = (checked) => {
  const icon = checked ? faStar : faEmptyStar;
  return <FontAwesomeIcon icon={icon} size="2x" />;
};
