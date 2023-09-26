import React, { Component } from "react";
import './loading.css';

export class Loading extends Component {

  componentDidMount() {
  }

  render() {
    return (
      
      <div id="loader-wrapper">
        <div id="loader"></div>
      </div>
    )
  }

}