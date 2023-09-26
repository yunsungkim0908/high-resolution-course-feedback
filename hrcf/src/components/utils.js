import Swal from "sweetalert2";

export const truncateString = (text, length) => {
  if (text.length <= length)
    return text
  return text.slice(0, length-4) + "..."
}

export const ErrorMessage = (errorMsg) => {
  console.log(errorMsg)
  Swal.fire({
    icon: "error",
    title: errorMsg
  })
}

export const SuccessMessage = (successMsg) => {
  Swal.fire({
    icon: "success",
    title: successMsg,
  })
}
