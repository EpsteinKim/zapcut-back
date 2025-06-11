export interface Segment {
    id: string
    type: 'voice' | 'background' | 'text'
    content: string
    start: number
    end: number
}

export interface Track {
    id: string
    label: string
    segments: Segment[]
} 