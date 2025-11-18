import { MongoClient } from 'mongodb';

const client = new MongoClient(process.env.MONGODB_URI);
const db = client.db(process.env.DB_NAME);

export class UserRepository {
  constructor(collectionName) {
    this.collection = db.collection(collectionName);
  }

  _buildRlsFilter(user, rlsFilter) {
    return {
      $and: [
        {
          $or: [
            { owner_email: user.email },
            { shared_users: { $in: [user.email] } },
            { org_id: user.orgId }
          ]
        },
        rlsFilter || {}
      ]
    };
  }

  async find(user, query = {}, rlsFilter = null) {
    return await this.collection.find({ ...query, ...this._buildRlsFilter(user, rlsFilter) }).toArray();
  }
}

export const Tm = new UserRepository("users");
