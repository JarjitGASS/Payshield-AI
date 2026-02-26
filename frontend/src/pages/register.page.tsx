import { useState } from "react";

export default function RegisterPage() {
  const [isError, setIsError] = useState<boolean | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;

    const formData = new FormData(form);


    try {
      const response = await fetch('http://localhost:3000/auth/register', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      setIsError(!result.success);
      setMessage(result.message);

    } catch (err) {
      console.error("Registration error:", err);
      setIsError(true);
      setMessage("Failed to connect to the server.");
    }
  };

  return (
    <div className="min-h-screen w-screen flex items-center justify-center bg-gray-100 p-6">
      <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-lg">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-8">Register</h1>
        
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="flex flex-col">
            <label className="text-sm font-semibold text-gray-600 mb-1">Nama Lengkap</label>
            <input name="fullname" type="text" required className="input-style text-black" placeholder="John Doe" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col">
              <label className="text-sm font-semibold text-gray-600 mb-1">Tempat Lahir</label>
              <input name="pob" type="text" required className="input-style text-black" placeholder="Jakarta" />
            </div>
            <div className="flex flex-col">
              <label className="text-sm font-semibold text-gray-600 mb-1">Tanggal Lahir</label>
              <input name="dob" type="date" required className="input-style text-black" />
            </div>
          </div>

          <div className="flex flex-col">
            <label className="text-sm font-semibold text-gray-600 mb-1">Jenis Kelamin</label>
            <select name="gender" required className="input-style bg-white text-black">
              <option value="">Pilih...</option>
              <option value="Laki-laki text-black">Laki-laki</option>
              <option value="Perempuan text-black">Perempuan</option>
            </select>
          </div>

          <div className="flex flex-col">
            <label className="text-sm font-semibold text-gray-600 mb-1">Foto ID Card (KTP/Passport)</label>
            <input 
              name="idCard" 
              type="file" 
              accept="image/*" 
              required 
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>

          <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition-all shadow-lg active:scale-[0.98]">
            Daftar Sekarang
          </button>
        </form>

        {isError !== null && (
          <div className={`mt-6 p-4 rounded-lg text-center ${isError ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
            {message}
          </div>
        )}
      </div>
    </div>
  );
}