import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export async function GET() {
  try {
    const filePath = path.join(process.cwd(), 'public', 'data', 'processed.json')
    
    // Check if file exists
    if (!fs.existsSync(filePath)) {
      return NextResponse.json(
        { error: 'Data file not found. Please run the data pipeline first.' },
        { status: 404 }
      )
    }

    const fileContents = fs.readFileSync(filePath, 'utf8')
    const data = JSON.parse(fileContents)

    return NextResponse.json(data)
  } catch (error) {
    console.error('Error reading data file:', error)
    return NextResponse.json(
      { error: 'Failed to load data' },
      { status: 500 }
    )
  }
}
