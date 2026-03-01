import { IoIosArrowBack } from "react-icons/io";

export default function GoToHomePage() {
  function handleButtonClick(){
    window.location.href = "/"
  }
  return (
    <button className="bg-white border border-blue-600 fixed top-10 left-10 rounded-full p-2 cursor-pointer hover:scale-105 transition-all w-15 h-15 flex items-center justify-center hover:shadow-2xl/30 active:scale-95" onClick={handleButtonClick}>
      <IoIosArrowBack size={24} className="text-black"/>
    </button>
  )
}