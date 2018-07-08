import deepchem as dc
import tensorflow as tf
from sklearn.metrics import accuracy_score

_, (train, valid, test), _ = dc.molnet.load_tox21()

train_X, train_y, train_w = train.X, train.y, train.w
valid_X, valid_y, valid_w = valid.X, valid.y, valid.w
test_X, test_y, test_w = test.X, test.y, test.w

train_y = train_y[:, 0]
valid_y = valid_y[:, 0]
test_y = test_y[:, 0]
train_w = train_w[:, 0]
valid_w = valid_w[:, 0]
test_w = test_w[:, 0]

d = 1024
n_hidden = 50
learning_rate = 0.001
n_epoch = 10
batch_size = 100
dropout_prob = 1.0

with tf.name_scope("placeholders"):
    x = tf.placeholder(tf.float32, (None, d))
    y = tf.placeholder(tf.float32, (None,))
    keep_prob = tf.placeholder(tf.float32)

with tf.name_scope("hidden-layer"):
    W = tf.Variable(tf.random_normal((d, n_hidden)))
    b = tf.Variable(tf.random_normal((n_hidden,)))
    x_hidden = tf.nn.relu(tf.matmul(x, W) + b)
    x_hidden = tf.nn.dropout(x_hidden, keep_prob)

with tf.name_scope("output"):
    W = tf.Variable(tf.random_normal((n_hidden, 1)))
    b = tf.Variable(tf.random_normal((1,)))
    y_logit = tf.matmul(x_hidden, W) + b
    y_one_prob = tf.sigmoid(y_logit)
    y_pred = tf.round(y_one_prob)

with tf.name_scope("loss"):
    y_expand = tf.expand_dims(y, 1)
    entropy = tf.nn.sigmoid_cross_entropy_with_logits(
        logits=y_logit, labels=y_expand)

    l = tf.reduce_sum(entropy)

with tf.name_scope("optim"):
    train_op = tf.train.AdamOptimizer(learning_rate).minimize(l)

with tf.name_scope("summaries"):
    tf.summary.scalar("loss", l)
    merged = tf.summary.merge_all()

train_writer = tf.summary.FileWriter(
    'tox21_fcnet_regularized', tf.get_default_graph())

N = train_X.shape[0]
with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())

    step = 0
    for epoch in range(n_epoch):
        pos = 0
        while pos < N:
            batch_x = train_X[pos:pos + batch_size]
            batch_y = train_y[pos:pos + batch_size]
            feed_dict = {x: batch_x, y: batch_y, keep_prob: dropout_prob}
            _, summary, loss = sess.run(
                [train_op, merged, l], feed_dict=feed_dict)
            print(f'epoch {epoch}, step {step}, loss :{loss} ')
            train_writer.add_summary(summary, step)

            step += 1
            pos += batch_size

    train_y_pred = sess.run(y_pred, feed_dict={x: train_X, keep_prob: 1.0})
    valid_y_pred = sess.run(y_pred, feed_dict={x: valid_X, keep_prob: 1.0})
    test_y_pred = sess.run(y_pred, feed_dict={x: test_X, keep_prob: 1.0})


train_weighted_score = accuracy_score(
    train_y, train_y_pred, sample_weight=train_w)
print("Train Weighted Classification Accuracy: %f" % train_weighted_score)
valid_weighted_score = accuracy_score(
    valid_y, valid_y_pred, sample_weight=valid_w)
print("Valid Weighted Classification Accuracy: %f" % valid_weighted_score)
test_weighted_score = accuracy_score(test_y, test_y_pred, sample_weight=test_w)
print("Test Weighted Classification Accuracy: %f" % test_weighted_score)
