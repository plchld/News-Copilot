export default function Header() {
  return (
    <header className="text-center py-8">
      <div className="inline-flex items-center space-x-2 mb-2">
        <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
          <span className="text-white font-bold text-sm">NC</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-800">
          News Copilot
        </h1>
      </div>
      <p className="text-gray-600">
        Κατανόηση Ελληνικών ειδήσεων με τεχνητή νοημοσύνη
      </p>
    </header>
  )
}