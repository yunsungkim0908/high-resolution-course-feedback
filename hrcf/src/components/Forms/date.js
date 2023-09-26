import React, { useState, useEffect } from 'react';
import { Field, useField } from "formik";

import DayPickerInput from 'react-day-picker/DayPickerInput'
import 'react-day-picker/lib/style.css';
import moment from 'moment';
import './date.css'

export const ClassBeginsPicker = (props) => {
  // Choose the first week of classes
  const [classBegins, classBeginsMeta, classBeginsHelpers] = useField("classBegins");
  const [firstWeek, firstWeekMeta, firstWeekHelpers] = useField("firstWeek");
  const [classBeginsDays, setClassBeginsDays] = useState(null)

  useEffect(() => {
    var newNumWeek = moment(firstWeek.value).startOf('week').diff(moment(classBegins.value).startOf('week'), 'week')
    if (isNaN(newNumWeek))
      newNumWeek = 1
    const datesInvalid = (newNumWeek <= 0) && (firstWeek.value !== "") && (classBegins.value !== "")
    classBeginsHelpers.setError(datesInvalid ? 'Invalid Dates' : undefined)
  }, [firstWeek.value])

  // const disableBefore = moment(new Date()).startOf('week').toDate();

  return (
    <div>
      <WeekPicker
        label="First Week of Class"
        selectedDays={classBeginsDays}
        setSelectedDays={setClassBeginsDays}
        field={classBegins}
        meta={classBeginsMeta}
        helpers={classBeginsHelpers}
        disableBefore={undefined}
        deselectToggle={props.deselectToggle}
      />
    </div>
  )
}

export const FirstWeekPicker = (props) => {
  const [firstWeek, firstWeekMeta, firstWeekHelpers] = useField("firstWeek");
  const [classBegins, classBeginsMeta, classBeginsHelpers] = useField("classBegins");
  const [numWeeks, numWeeksMeta, numWeeksHelpers] = useField("numWeeks")
  const [lastWeek, lastWeekMeta, lastWeekHelpers] = useField("lastWeek");
  const [firstDays, setFirstDays] = useState(null)

  useEffect(() => {
    var newNumWeek = moment(lastWeek.value).startOf('week').diff(moment(firstWeek.value).startOf('week'), 'week') + 1
    if (isNaN(newNumWeek))
      newNumWeek = 0
    const datesInvalid = (newNumWeek <= 0) && (firstWeek.value !== "") && (lastWeek.value !== "")
    numWeeksHelpers.setValue((!datesInvalid) ? newNumWeek : 0)
    firstWeekHelpers.setError(datesInvalid ? 'Invalid Dates' : undefined)
  }, [firstWeek.value, lastWeek.value, classBegins.value])

  const disableBefore = moment(new Date())
      .add(1, 'week').startOf('week').toDate();

  return (
    <div>
      <WeekPicker
        label="Week of Last Survey"
        selectedDays={firstDays}
        setSelectedDays={setFirstDays}
        field={firstWeek}
        meta={firstWeekMeta}
        helpers={firstWeekHelpers}
        disableBefore={disableBefore}
        deselectToggle={props.deselectToggle}
      />
    </div>
  )
}

export const LastWeekPicker = (props) => {
  const [firstWeek, firstWeekMeta, firstWeekHelpers] = useField("firstWeek");
  const [numWeeks, numWeeksMeta, numWeeksHelpers] = useField("numWeeks")
  const [lastWeek, lastWeekMeta, lastWeekHelpers] = useField("lastWeek");
  const [lastDays, setLastDays] = useState(null)

  useEffect(() => {
    var newNumWeek = moment(lastWeek.value).startOf('week').diff(moment(firstWeek.value).startOf('week'), 'week') + 1
    if (isNaN(newNumWeek))
      newNumWeek = 0
    const datesInvalid = (newNumWeek <= 0) && (firstWeek.value !== "") && (lastWeek.value !== "")
    numWeeksHelpers.setValue((!datesInvalid) ? newNumWeek : 0)
    lastWeekHelpers.setError(datesInvalid ? 'Invalid Dates' : null)
  }, [firstWeek.value, lastWeek.value])

  const disableBefore = moment(new Date())
      .add(1, 'week').startOf('week').toDate();

  return (
    <div>
      <WeekPicker
        label="Week of Last Survey"
        selectedDays={lastDays}
        setSelectedDays={setLastDays}
        field={lastWeek}
        meta={lastWeekMeta}
        helpers={lastWeekHelpers}
        disableBefore={disableBefore}
        deselectToggle={props.deselectToggle}
      />
    </div>
  )
}

export const WeekPicker = ({
    label, selectedDays, setSelectedDays,
    field, meta, helpers, deselectToggle, disableBefore
  }) => {
  const [hoverRange, setHoverRange] = useState(null)
  const [modifiers, setModifiers] = useState({})

  const getWeekDays = (weekStart) => {
    const days = [weekStart];
    for (let i = 1; i < 7; i += 1) {
      days.push(
        moment(weekStart)
          .add(i, 'days')
          .toDate()
      );
    }
    return days;
  }

  const getWeekRange = (date) => {
    return {
      from: moment(date)
        .startOf('week')
        .toDate(),
      to: moment(date)
        .endOf('week')
        .toDate(),
    };
  }

  useEffect(() => {
    setSelectedDays(null)
    setHoverRange(null)
  }, [deselectToggle])

  useEffect(() => {
    const daysAreSelected = (selectedDays == null)
      ? 0 : selectedDays.length > 0;

    const newModifiers = {
      hoverRange: hoverRange,
      selectedRange: daysAreSelected && {
        from: selectedDays[0],
        to: selectedDays[6],
      },
      hoverRangeStart: hoverRange && hoverRange.from,
      hoverRangeEnd: hoverRange && hoverRange.to,
      selectedRangeStart: daysAreSelected && selectedDays[0],
      selectedRangeEnd: daysAreSelected && selectedDays[6],
    };

    setModifiers(newModifiers)
  }, [selectedDays, hoverRange])

  return (
    <div>
      <div className="week-picker">
        <label style={{'marginRight': '10px'}}>
          Week of 
        </label>
        <DayPickerInput
          inputProps={{ style: {width: 100, textAlign: 'center'}}}
          onDayChange={(date) => {
            helpers.setValue(moment(date).format("MM/DD/YYYY"))
            setSelectedDays(getWeekDays(getWeekRange(date).from))}}
          value={field.value}
          dayPickerProps={{
            selectedDays: selectedDays,
            modifiers: modifiers,
            disabledDays: [{before: disableBefore}, {daysOfWeek: [0,6]}],
            showWeekNumbers: true,
            showOutsideDays: true,
            onDayMouseEnter: (date) => {
              setHoverRange(getWeekRange(date))},
            onDayMouseLeave: (date) => {
              setHoverRange(undefined)},
          }}
        />
      </div>

      {meta.error &&
        <div className="error-space">
         <span className="error">{meta.error}</span>
        </div>
      }
    </div>
  )
}
