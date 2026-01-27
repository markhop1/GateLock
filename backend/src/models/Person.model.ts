import mongoose, { Schema, Document } from 'mongoose'

export interface IPerson extends Document {
  name: string
  email?: string
  photoUrl?: string
  userId: mongoose.Types.ObjectId
  createdAt: Date
  updatedAt: Date
}

const personSchema = new Schema<IPerson>(
  {
    name: {
      type: String,
      required: [true, 'Name is required'],
      trim: true,
    },
    email: {
      type: String,
      trim: true,
      lowercase: true,
      match: [/^\S+@\S+\.\S+$/, 'Please provide a valid email'],
    },
    photoUrl: {
      type: String,
      trim: true,
    },
    userId: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      index: true,
    },
  },
  {
    timestamps: true,
  }
)

// Index for faster queries
personSchema.index({ userId: 1, name: 1 })

export const Person = mongoose.model<IPerson>('Person', personSchema)
